from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import SystemMessage,HumanMessage, ToolMessage
import json
from tools import get_loan_status,get_emi_schedule
load_dotenv()




tools = [get_loan_status,get_emi_schedule]

model = ChatOpenAI(model="gpt-4o-mini")
model_with_tool = model.bind_tools(tools)

system = SystemMessage(content="You are a Bajaj Finance support agent. Use tools for real data.")



tool_map = {
    "get_loan_status": get_loan_status,
    "get_emi_schedule":get_emi_schedule

}


run = 'user'
while run:
    questions = input('ask questions :')
    user_msg = HumanMessage(content=questions)
    messages = [system,user_msg]
    response = model_with_tool.invoke(messages)
    messages.append(response)
    if response.tool_calls:
        print('calling tools')
        tool_result = []
        for i in response.tool_calls:
            tool_name = i['name']
            tool_args = i['args']
            tool_id = i['id']
            result = tool_map[tool_name].invoke(tool_args)
            tool_result.append((tool_id,result,tool_name))
        for tool_id, result,tool_name in tool_result:
            tool_msg = ToolMessage(content=str(result),tool_call_id=tool_id)
            messages.append(tool_msg)

    
    final_result = model_with_tool.invoke(messages)
    print('AI response: ',final_result.content)
    if questions =='exit':
        break



        











# pass the input to model
response = model_with_tool.invoke(messages)
messages.append(response)

tool_map = {
    "get_loan_status": get_loan_status,
    "get_emi_schedule":get_emi_schedule

}

tool_result = []

# tool executions
for i in response.tool_calls:
    tool_name = i['name']
    tool_args = i['args']
    tool_id = i['id']
    result = tool_map[tool_name].invoke(tool_args)
    tool_result.append((tool_id,result,tool_name))

# result from tools
for tool_id, result,tool_name in tool_result:
    tool_msg = ToolMessage(content=str(result),tool_call_id=tool_id)
    messages.append(tool_msg)


final_response = model_with_tool.invoke(messages)
print('Final response: ',final_response.content)