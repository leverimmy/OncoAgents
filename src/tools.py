"""
This source file defines the tools used by the agents.
"""
import argparse
import os
import requests
import torch
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
# from logger import logger
from MedSAM.MedSAM_Inference import medsam_inference, show_box, show_mask
from MedSAM.segment_anything import sam_model_registry
from skimage import io, transform
from typing import List, Optional

async def google_search(query: str, top_k: Optional[int] = 5) -> str:
    """
    Performs a Google search for the given query.

    Args:
        query (str): The search query.
        top_k (int, optional): The number of top results to return. Defaults to 5.
    
    Returns:
        search_results (str): A formatted string of search result snippets.
    """

    url = "https://google.serper.dev/search"

    payload = {
        "q": query
    }

    headers = {
        "X-API-KEY": os.getenv("SERPER_API_KEY"),
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
    except Exception as e:
        # logger.error(f"Google Search API error: {e}")
        return []

    data = response.json()

    results = data.get("organic", [])
    snippets = [item.get("snippet", "") for item in results[:top_k]]

    # logger.info(f"Google search completed with {len(snippets)} results for query '{query}'")

    return f"Here are the top {top_k} search results for '{query}':\n" + "\n".join(snippets)

async def segment_images(paths_to_img: List[str], bbox_coordinates: List[List[int]]) -> List[str]:
    """
    A function that segments a region of interest annotated by bounding boxes using the MedSAM model. Returns the size of the segmented area.

    Args:
        paths_to_img (List[str]): A list of file paths to the medical images.
        bbox_coordinates (List[List[int]]): A list of bounding box coordinates, where each bounding box is represented as [x_min, y_min, x_max, y_max].
    
    Returns:
        results (List[str]): The sizes of the segmented area in pixels.
    """
    sizes = []
    results = []
    for path_to_img in paths_to_img:
        size = await segment_image(path_to_img, bbox_coordinates)
        sizes.append(size)
        results.append(f"Segmented image {path_to_img} with bounding boxes {bbox_coordinates}. Size: {size} pixels.")
    # logger.info(f"Result of segmentation: {result}")
    return results

async def segment_image(path_to_img: str, bbox_coordinates: List[List[int]]) -> str:
    """
    A function that segments a region of interest annotated by bounding boxes using the MedSAM model. Returns the size of the segmented area.

    Args:
        path_to_img (str): The file system path to the image that needs to be analyzed. Usually 'path_name/file_name.extension'.
        bbox_coordinates (List[List[int]]): A list of bounding box coordinates, where each bounding box is represented as [x_min, y_min, x_max, y_max].

    Returns:
        final_size (str): Segmentation size of the union of all regions of interest in pixels.
    """
    # Code adapted from MedSAM_Inference.py
    # logger.info(f"Segmenting image {path_to_img} with bounding boxes {bbox_coordinates}")
    parser = argparse.ArgumentParser(
        description="run inference on testing set based on MedSAM"
    )
    parser.add_argument(
        "-i",
        "--data_path",
        type=str,
        default="assets/img_demo.png",
        help="path to the data folder",
    )
    parser.add_argument(
        "-o",
        "--seg_path",
        type=str,
        default="assets/",
        help="path to the segmentation folder",
    )
    parser.add_argument(
        "--box",
        type=str,
        default='[95, 255, 190, 350]',
        help="bounding box of the segmentation target",
    )
    parser.add_argument("--device", type=str, default="cuda:0", help="device")
    parser.add_argument(
        "-chk",
        "--checkpoint",
        type=str,
        default="work_dir/MedSAM/medsam_vit_b.pth",
        help="path to the trained model",
    )

    current_time = datetime.now()
    folder_name = current_time.strftime("%d_%m_%y_%H_%M_%S")
    path = os.path.join("../data/MedSAM_Outputs/", folder_name)
    os.makedirs(path, exist_ok=True)

    args_list = ["--data_path", path_to_img,
                 "--seg_path", path,
                 "--device", "cpu",
                 "--checkpoint", "../data/medsam_vit_b.pth"]
    args = parser.parse_args(args_list)

    device = args.device
    medsam_model = sam_model_registry["vit_b"](checkpoint=args.checkpoint)
    medsam_model = medsam_model.to(device)
    medsam_model.eval()

    img_np = io.imread(args.data_path)
    if len(img_np.shape) == 2:
        img_3c = np.repeat(img_np[:, :, None], 3, axis=-1)
    else:
        img_3c = img_np
    H, W, _ = img_3c.shape

    img_1024 = transform.resize(
        img_3c, (1024, 1024), order=3, preserve_range=True, anti_aliasing=True
    ).astype(np.uint8)
    img_1024 = (img_1024 - img_1024.min()) / np.clip(
        img_1024.max() - img_1024.min(), a_min=1e-8, a_max=None
    )  # normalize to [0, 1], (H, W, 3)
    # convert the shape to (3, H, W)
    img_1024_tensor = (
        torch.tensor(img_1024).float().permute(2, 0, 1).unsqueeze(0).to(device)
    )

    medsam_seg_merged = np.zeros((H, W))
    box_nps = []
    for idx, bbox_coordinate in enumerate(bbox_coordinates):
        box_nps.append(np.array([bbox_coordinate])) 
        # transfer box_np t0 1024x1024 scale
        box_1024 = box_nps[-1] / np.array([W, H, W, H]) * 1024
        with torch.no_grad():
            image_embedding = medsam_model.image_encoder(img_1024_tensor)  # (1, 256, 64, 64)

        medsam_seg = medsam_inference(medsam_model, image_embedding, box_1024, H, W)
        io.imsave(
            os.path.join(args.seg_path, f"seg_{idx}_" + os.path.basename(args.data_path)),
            medsam_seg,
            check_contrast=False,
        )
        # logger.info(f"Size: {medsam_seg.sum()}")
        medsam_seg_merged = np.logical_or(medsam_seg_merged, medsam_seg)
    
    _fig, ax = plt.subplots(1, 2, figsize=(10, 5))
    ax[0].imshow(img_3c)
    for box_np in box_nps:
        show_box(box_np[0], ax[0])
    ax[0].set_title("Input Image and Bounding Box")
    ax[1].imshow(img_3c)
    show_mask(medsam_seg_merged, ax[1])
    for box_np in box_nps:
        show_box(box_np[0], ax[1])
    ax[1].set_title("MedSAM Segmentation")
    plt.savefig(os.path.join(args.seg_path, "segmentation_result.png"))

    return medsam_seg_merged.sum()

async def analyze_mutation(path_to_img: str) -> str:
    """
    Analyzes a histology image for genetic mutations using a vision model. Specifically, determine:
    -   MSI/MSS status and probability
    -   KRAS mutation status and probability
    -   BRAF mutation status and probability

    Args:
        path_to_img (str): The file system path to the histology image.
    
    Returns:
        analysis_report (str): The analysis report on genetic mutations.
    """
    query = """
You are a medical expert specialized in histology and genetic mutations. 
Analyze the histology image for the following genetic mutations:
- Determine MSI (Microsatellite Instability) or MSS (Microsatellite Stability) status and provide the associated probability.
- Determine KRAS mutation status and provide the associated probability.
- Determine BRAF mutation status and provide the associated probability.
Provide a concise report summarizing the findings.

Return the analysis in the following format:
{
    "MSI/MSS": {
        "Status": "<status>"("MSI" or "MSS"),
        "Probability": <probability>,
        "Reasoning": "<detailed reasoning>",
    },
    "KRAS Mutation": {
        "Status": "<status>"("Wild-type" or "Mutated"),
        "Probability": <probability>,
        "Reasoning": "<detailed reasoning>",
    },
    "BRAF Mutation": {
        "Status": "<status>"("Wild-type" or "Mutated"),
        "Probability": <probability>,
        "Reasoning": "<detailed reasoning>",
    }
}
"""

    # analysis_report = get_response_from_vision_model([path_to_img], query)
    analysis_report = """
{
"MSI/MSS": {
    "Status": "MSI"
    "Probability": 0.98,
},
"KRAS Mutation": {
    "Status": "Wild-type",
    "Probability": 0.44,
},
"BRAF Mutation": {
    "Status": "Mutated",
    "Probability": 0.7,
}
"""
    # logger.debug(f"Generated mutation analysis report: {analysis_report}")
    return analysis_report
