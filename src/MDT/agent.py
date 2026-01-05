from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from backend import *
from prompt import *
from MDT.tools import *
from rag_module import get_persistent_memory

# 影像科医生
radiologist_memory = get_persistent_memory("radiologist")
radiologist_agent = AssistantAgent(
    name="radiologist_agent",
    model_client=model_client,
    tools=[google_search],
    system_message=RADIOLOGIST_SYSTEM_MESSAGE,
    reflect_on_tool_use=True,
    max_tool_iterations=5,
    # model_client_stream=True,
    memory=[radiologist_memory],
)

# 病理科医生
pathologist_memory = get_persistent_memory("pathologist")
pathologist_agent = AssistantAgent(
    name="pathologist_agent",
    model_client=model_client,
    tools=[google_search],
    system_message=PATHOLOGIST_SYSTEM_MESSAGE,
    reflect_on_tool_use=True,
    max_tool_iterations=5,
    # model_client_stream=True,
    memory=[pathologist_memory],
)

# 放射科医生
radiation_oncologist_memory = get_persistent_memory("radiation_oncologist")
radiation_oncologist_agent = AssistantAgent(
    name="radiation_oncologist_agent",
    model_client=model_client,
    tools=[google_search],
    system_message=RADIATION_ONCOLOGIST_SYSTEM_MESSAGE,
    reflect_on_tool_use=True,
    max_tool_iterations=5,
    # model_client_stream=True,
    memory=[radiation_oncologist_memory],
)

# 外科医生
surgeon_memory = get_persistent_memory("surgeon")
surgeon_agent = AssistantAgent(
    name="surgeon_agent",
    model_client=model_client,
    tools=[google_search],
    system_message=SURGEON_SYSTEM_MESSAGE,
    reflect_on_tool_use=True,
    max_tool_iterations=5,
    # model_client_stream=True,
    memory=[surgeon_memory],
)

# 肿瘤内科医生
medical_oncologist_memory = get_persistent_memory("medical_oncologist")
medical_oncologist_agent = AssistantAgent(
    name="medical_oncologist_agent",
    model_client=model_client,
    tools=[google_search],
    system_message=MEDICAL_ONCOLOGIST_SYSTEM_MESSAGE,
    reflect_on_tool_use=True,
    max_tool_iterations=5,
    # model_client_stream=True,
    memory=[medical_oncologist_memory],
)

# 首席专家医生，协调各科医生
chief_expert_memory = get_persistent_memory("chief_expert")
chief_expert_agent = AssistantAgent(
    name="chief_expert_agent",
    model_client=model_client,
    tools=[google_search],
    system_message=CHIEF_EXPERT_SYSTEM_MESSAGE,
    reflect_on_tool_use=True,
    max_tool_iterations=5,
    # model_client_stream=True,
    memory=[chief_expert_memory],
)

user_proxy = UserProxyAgent("user_proxy", input_func=input)
