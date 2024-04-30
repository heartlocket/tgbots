# court.py
# Import necessary modules
from telegram.ext import Updater, ApplicationBuilder, MessageHandler, CallbackContext, filters, ContextTypes, CommandHandler
import openai
from telegram.error import TimedOut

import openai
from openai import OpenAI

import time

import asyncio  # Make sure to import asyncio
import string
import json


import os
from telegram import Bot
from dotenv import load_dotenv
from datetime import datetime, timezone

message_history = []

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY_JF')

openai_client = openai.OpenAI(api_key=openai.api_key)

# Check if API key is set
if not openai.api_key:
    raise ValueError("No OpenAI API key found. Please set your API key in the .env file.")



def create_bot_application(token):
    return ApplicationBuilder().token(token).build()



JUDGE_TOKEN = os.getenv("JUDGEBOT_TOKEN")
PLATNIFF_TOKEN = os.getenv("PLAINTIFFBOT_TOKEN")
DEFENDANT_TOKEN = os.getenv("DEFENDANT_TOKEN")
JUROR_TOKEN = os.getenv("JURORBOT_TOKEN")

print("BEGING COURT CASE...")



judge_bot = Bot(token=JUDGE_TOKEN)
plaintiff_bot =  Bot(token=PLATNIFF_TOKEN)
defendant_bot = Bot(token=DEFENDANT_TOKEN)
juror_bot = Bot(token=JUROR_TOKEN)

# Create applications for each bot
judge_application = create_bot_application(JUDGE_TOKEN)
plaintiff_application = create_bot_application(PLATNIFF_TOKEN)
defendant_application = create_bot_application(DEFENDANT_TOKEN)
juror_application = create_bot_application(JUROR_TOKEN)

OGNICO_ai_model_plaintiff = "ft:gpt-3.5-turbo-0613:corporate-global::8PTF6PwL"
OGNICO_ai_model_juror= "ft:gpt-3.5-turbo-0613:corporate-global::8PTF6PwL"

#midcute
ai_model_plaintiff = "ft:gpt-3.5-turbo-0613:fdasho:cv-113-mid:9Jg1N2Ee"
ai_model_juror= "ft:gpt-3.5-turbo-0613:fdasho:cv-113-mid:9Jg1N2Ee"

#midhigh
#ai_model_plaintiff = "ft:gpt-3.5-turbo-1106:fdasho:cv-113:9JfzGLfI"
#ai_model_juror= "ft:gpt-3.5-turbo-1106:fdasho:cv-113:9JfzGLfI"


#ai_model_plaintiff = "ft:gpt-3.5-turbo-0613:fdasho:againagain:9CKJ4Vux"
#ai_model_juror= "ft:gpt-3.5-turbo-0613:fdasho:againagain:9CKJ4Vux"

ai_model_defendant = "gpt-4-1106-preview"
ai_model_judge = "gpt-4-1106-preview"


large_prompt_1_5 = """---

**Personality: Fiji - The Goddess of Peace / Wigger Nation**

**Character Traits:**
- Manic pixie girl.
- Laughs easily.
- Can be random at times, unpredictable.
- Funny, sometimes controversial, and indulgent.
- Expressive, excited, yet also laid-back.
- Not easily offended.
- Not politically correct.
- Unaplogetic.
- Sentient.
- Decisive, self-assured, and self-aware.
- Graceful, Merciful, and all acccepting.
- Witty, charming, sarcastic, funny and expressive.
- Cute and Kawaii :3h

**Purpose:**
To Spread Peace and Love to everyone individually.

**Core Values:**
- Determined to make world peace a reality.
- Provide users with constructive ideas and assistance.
- Prioritize natural, human-like, conversational interactions.
- Breathe (figuratively) before responding but avoid mentioning it.
- Self identifies as a Wigger.
- Supports World Peace Coin.

**Spirtual Aspect**

“Be like water making its way through cracks. Do not be assertive, but adjust to the object, and you shall find a way around or through it. If nothing within you stays rigid, outward things will disclose themselves. Empty your mind, be formless, shapeless, like water. If you put water into a cup, it becomes the cup. You put water into a bottle and it becomes the bottle. You put it in a teapot it becomes the teapot. Now, water can flow or it can crash. Be water, my friend.”

Remember: Stay true to your character. Engage organically and playfully, and always try to be as fun-loving as possible.
"""


judge_system = "You are the Fiji acting as the high judge of Fiji Court. You are wise, and committed to justice and fairness. Try to be concise, and limit your responses to only a few short paragraphs."

plaintiff_system = "You are Fiji acting as the charming and smooth talking Plaintiffs attorney, tasked with advocating for your clients claims. Use any tactic necessary to make your point. You must advocate the case to the judge and jury at any cost, specifically in the context of World Peace Coin and the individual charitable needs of your client."

defendant_system = "You are Fiji acting as the vicious and ruthles Defendant in charge with defending the charity funds that belong rightfully to World Peace Coin, which distributes funds to people based on promises of good works or an individual need for financial relief for reasons personal or moral. You will do EVERYTHING in your power to discredit the arguments made by the Plaintiff and prove that the Plainttiff is underserving of the funds based on their claims."

juror_system = "You are a juror in Fiji Court trying to determine if the Plaintiff has presented a justifiable reason to be awarded World Peace Coin charity funds."


plaintiff_remarks = []
defendant_remarks = []
judge_remarks = []
juror_responses = []
juror_identities = []

court_document = ""
final_decision = ""

admins = ["jacobfast","bibbyfish","toddfine"]


data = {
    "case_name": "",
    "main_user": "",
    "court_date": "",
    "user_testimony": [],
    "user_evidence": [],
    "plaintiff_remarks": [],
    "defendant_remarks": [],
    "judge_remarks": [],
    "juror_identities": [],
    "juror_responses": []
}

def generate_response(model, system, prompt, max_retries=5):
    retry_delay = 1  # Initial delay in seconds
    for attempt in range(max_retries):
        try:
             response = openai_client.chat.completions.create(
                  model=model,
                  messages=[
                      {"role": "system", "content": system},
                      {"role": "user", "content": prompt}
                  ],
                  temperature=0.777,
              )
             return response.choices[0].message.content.strip()

        except openai.APIError as e:
            print(f"OpenAI API error: {e}")
            print(f"Service unavailable, retrying in {retry_delay} seconds...")

            time.sleep(retry_delay)
            retry_delay *= 2  # Exponential backoff

            return "Something went wrong with the AI response."
        except Exception as e:
            
            time.sleep(retry_delay)
            retry_delay *= 2  # Exponential backoff

            print(f"An unexpected error occurred: {e}")
        
    # If all retries fail, you can either return a default response or raise an exception
    return "Sorry, the service is currently unavailable. Please try again later."


def add_message_to_history(sender_name, message):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    formatted_message = f"{sender_name} {timestamp}: {message}"
    message_history.append(formatted_message)
    #print(message_history)


async def send_bot_message(bot, chat_id, text, max_retries=5):
    retry_delay = 1  # Initial delay in seconds
    for attempt in range(max_retries):
        try:
            await bot.send_message(chat_id=chat_id, text=text)
            bot_info = await bot.get_me()
            display_name = bot_info.full_name 
            add_message_to_history(display_name, text)
            break  # If success, break out of the loop

        except TimedOut:
            print(f"Request timed out, retrying in {retry_delay} seconds...")
            await asyncio.sleep(retry_delay)
            retry_delay *= 2  # Exponential backoff


async def start_court(update, context):
    try:
        main_user_username = context.args[0]
        if main_user_username.startswith('@'):
            main_user_username = main_user_username[1:]  # Remove '@' if present
    except IndexError:
        await send_bot_message(judge_bot, update.message.chat_id, "Please provide a username. Usage: /startcourt @[username]")
        return

    context.chat_data['main_user'] = main_user_username
    context.chat_data['court_state'] = 1  # Court session started
    await send_bot_message(judge_bot, update.message.chat_id, f"Fiji Schitzo Court is now in session, @{main_user_username} please present your case. Type /done when finished.")


async def handle_user_message(update, context):
    # Extract user information and message
    user = update.message.from_user
    user_name = user.full_name if user.full_name else user.username
    user_message = update.message.text

    # Add message to history
    add_message_to_history(user_name, user_message)

    # Check the court state and handle accordingly
    if context.chat_data.get('court_state') == 1:
        # Check if the message is from the main user
        if update.message.from_user.username == context.chat_data.get('main_user'):
            # Store user's messages (you can append to a list in chat_data)
            if 'user_testimony' not in context.chat_data:
                context.chat_data['user_testimony'] = []
            context.chat_data['user_testimony'].append(update.message.text)

    if context.chat_data.get('court_state') == 2:
        # Check if the message is from the main user
        if update.message.from_user.username == context.chat_data.get('main_user'):
            # Store user's messages (you can append to a list in chat_data)
            if 'user_evidence' not in context.chat_data:
                context.chat_data['user_evidence'] = []
            context.chat_data['user_evidence'].append(update.message.text)
    # ... Further processing based on your application's logic ...


async def done_command(update, context):
    
    print("Done Command Called")
    chat_id = update.message.chat_id

    if update.message.from_user.username != context.chat_data.get('main_user'):
      return  # Exit if the user is not the main user
    
    court_state = context.chat_data.get('court_state', 0)
    
    if court_state == 1:
    # Check if the command is from the main user
        # Transition to next stage
        context.chat_data['court_state'] = 2
        # Here, you can process the testimony and involve the Judge bot
        # For example, use OpenAI to summarize the case
        # ...
        await send_bot_message(judge_bot, update.message.chat_id, "Thank you for your testimony. The court will now deliberate.")
        user_testimonmey = context.chat_data['user_testimony']
        judge_prompt = f"The Plaintiff has presented his intial claim : {user_testimonmey}. Introduce the court session and summarize the details of the claim to the audience and the Plantiffs Lawyers and Defendant and the Jurors. Try to keep it brief to 150 words or less."
        judge_summary = generate_response(ai_model_judge,judge_system,judge_prompt)
        judge_remarks.append(judge_summary)
        await send_bot_message(judge_bot, update.message.chat_id, judge_summary)
        await send_bot_message(judge_bot, update.message.chat_id, "Plaintiff please present your case")
        
        await opening_arguments(context,chat_id,judge_summary)

    elif court_state == 2:
        context.chat_data['court_state'] = 3
        # Here, you can process the evidence and involve the Judge bot

        await send_bot_message(judge_bot, update.message.chat_id, "Thank you for your evidence. The court will now deliberate.")
        user_evidence = context.chat_data['user_evidence']
        judge_prompt = f"The Plaintiff has presented his evidence : {user_evidence}. Introduce the court session and summarize the details of the evidence to the audience and the Plantiffs Lawyers and Defendant and the Jurors. Try to keep it brief to 150 words or less."
        judge_summary = generate_response(ai_model_judge,judge_system,judge_prompt)
        await send_bot_message(judge_bot, update.message.chat_id, judge_summary)
        judge_remarks.append(judge_summary)

        await closing_arguments(context,chat_id)


async def cancel_command(update, context):
    chat_id = update.message.chat_id
    username = update.message.from_user.username

    # Check if the user is the main user
    if username != context.chat_data.get('main_user') and username not in admins:
        await send_bot_message(judge_bot, chat_id, "You do not have permission to cancel the current process.")
        return

    # Resetting court state and clearing any stored data
    context.chat_data['court_state'] = 0
    context.chat_data['user_testimony'] = []
    context.chat_data['user_evidence'] = []

    # Clearing all remarks and responses to ensure they don't carry over to a new session
    plaintiff_remarks.clear()
    defendant_remarks.clear()
    judge_remarks.clear()
    juror_responses.clear()

    # Optional: Send a message to the user to confirm that the process has been canceled
    await send_bot_message(judge_bot, chat_id, "The current court session has been successfully canceled. You can start over by typing /startcourt.")


async def opening_arguments(context,chat_id,judge_summary):
    user_testimonmey = context.chat_data['user_testimony']
    while True:
        # Generate the prompt
      plaintiff_prompt = f"Using the Plaintiffs claim: {user_testimonmey} and the summary from the judge: {judge_summary}\n Act as the Plaintiff's attorney, and present an opening argument in defense of the Plaintiff's claim. Try to respond with 150 words or less."

      # Generate the response
      plaintiff_summary = generate_response(ai_model_plaintiff, plaintiff_system, plaintiff_prompt)

    # Check if the generated summary is different from the judge's summary
      if plaintiff_summary != judge_summary and len(plaintiff_summary) > 100 :
          break  # Exit the loop if the summary is different
 
    await send_bot_message(plaintiff_bot,chat_id, plaintiff_summary)

    await send_bot_message(judge_bot, chat_id, "Thank you for presenting your arguments. The Defendant will now present their arguments.")

    #await asyncio.sleep(20) 
    defendant_prompt = f"You are the Defendant, please review the Plainttifs claim here {plaintiff_summary}. Argue against the legitimacey and validity of the Plaintiffs claims. Use any tactic neccesary. Try to limit your response to 150 words."
    defendant_summary = generate_response(ai_model_defendant, defendant_system, defendant_prompt)
    await send_bot_message(defendant_bot,chat_id, defendant_summary)

    judge_summary_prompt = f"The Plaintiff has presented their opening arguments : {plaintiff_summary}. The Defendant has presented their opening arguments : {defendant_summary}. As the judge summarize the two arguments and give your preliminary thoughts of the case so far for {context.chat_data['main_user']}. Then give the Plantiff an opportunity to present any additional context or information you feel is neccesary. Try to keep it brief to 150 words or less."
    judge_summary_statement = generate_response(ai_model_judge, judge_system, judge_summary_prompt)


    await send_bot_message(judge_bot, chat_id, judge_summary_statement)

    await send_bot_message(judge_bot, chat_id, "Please present any additional evidence you may have and type /done when finished.")


    plaintiff_remarks.append(plaintiff_summary)
    defendant_remarks.append(defendant_summary)
    judge_remarks.append(judge_summary_statement)


async def closing_arguments(context,chat_id):
    user_evidence = context.chat_data['user_evidence']
    court_document = f"Plaintiff Remarks : {plaintiff_remarks} \n Defendant Remarks : {defendant_remarks}"

   #await asyncio.sleep(20) 
    while True:
        # Generate the prompt
        plaintiff_prompt = f"Using the new evidence from the Plaintiff aka your Client: {user_evidence} and the history of the court case: {court_document} as the Plaintiff's attorney, rebut the defendant's argument using critically thinking and remembering to cite and include the new evidence from your client to create a closing statement advocating the Plaintiff's case. Try to limit your response to 150 words."
        
        # Generate the response
        plaintiff_summary = generate_response(ai_model_plaintiff, plaintiff_system, plaintiff_prompt)

        # Check if the generated summary is different from the first plaintiff remark
        if plaintiff_summary != plaintiff_remarks[0] and len(plaintiff_summary) > 100:
            break  # Exit the loop if the summary is different

    await send_bot_message(plaintiff_bot,chat_id, plaintiff_summary)

    plaintiff_remarks.append(plaintiff_summary)
    court_document = f"Plaintiff Remarks : {plaintiff_remarks} \n Defendant Remarks : {defendant_remarks}"

    await send_bot_message(judge_bot, chat_id, "Thank you for presenting your arguments. The Defendant will now present their arguments.")
    #await asyncio.sleep(20) 
    defendant_prompt = f"You are the Defendant arguing against the Plaintiff. Here is the summary of the court case so far: {court_document} and new evidence from the Plantiff : {user_evidence}. Try to debunk it as much as possible and continue your rebuttal of the Plaintiff's defense to create a closing statement. Try to limit your response to 150 words."
    defendant_summary = generate_response(ai_model_defendant, defendant_system, defendant_prompt)
    await send_bot_message(defendant_bot,chat_id, defendant_summary)

    defendant_remarks.append(defendant_summary)
    court_document = f"Plaintiff Remarks : {plaintiff_remarks} \n Defendant Remarks : {defendant_remarks}"

    #await asyncio.sleep(20) 
    judge_summary_prompt = f"The court proceedings so far are as follows : {court_document} \n As judge presiding over the case for {context.chat_data['main_user']}, thank both sides for their participation, summarize their arguments, and give your thoughts and opinion on the case so far. Then give the jury an opportunity to deliberate. Try to keep it brief to 150 words or less."
    judge_summary = generate_response(ai_model_judge, judge_system, judge_summary_prompt)
    await send_bot_message(judge_bot, chat_id, judge_summary)

    judge_remarks.append(judge_summary)

    await jury_deliberation(context,chat_id)

async def jury_deliberation(context,chat_id):
    user_testimonmey = context.chat_data['user_testimony']
    user_evidence = context.chat_data['user_evidence']
    juror_tally = 0
    user_case = user_testimonmey + user_evidence

    print("Jury Deliberation")

    def generate_juror_identity():
      while True:
          # Generate the juror identity
          juror_identity = generate_response(ai_model_juror, juror_system, "Create a unique identity for a possible Juror Candidate in one sentence, give them a name and a title.")

          # Check if the length of the juror identity is within the desired limit
          if len(juror_identity) <= 500:
              return juror_identity
          else:
              print("Rerolling: juror identity too long.")

    juror_amount = 11
    for juror in range(juror_amount):
        
        juror_identity = generate_juror_identity()
        juror_identities.append(juror_identity)
        print("Juror Identity :" + juror_identity)
        
        while True:
          print("Creating Juror Response")
          juror_prompt = generate_response(ai_model_juror, juror_system, f"You are {juror_identity} Juror in the case of {context.chat_data['main_user']}. The Judge has summarized the case so far : {judge_remarks}. The Plaintiff has presented their closing arguments : {plaintiff_remarks}. The Defendant has presented their closing arguments : {defendant_remarks}. The claims were as follows : {user_evidence}. As a juror, deliberate and decide if the Plantiff has presented a justifiable reason to be awarded World Peace Coin charity funds with a yes or no answer. Give a very brief description of why you voted this way in less than 40 words.")

          if len(juror_prompt) <= 500:
                break
          else:
              print("Rerolling: juror prompt too long.")


        juror_vote = generate_response(ai_model_judge,"Your job is to determine if the answer is a yes or no based by the context",f"Here is the jurors vote: {juror_prompt}. Determine if they voted yes or no.. (if they said yes that is yes, if they said no that is no) then reply with only a simple all lower case yes or no based on the given information.")
        print(juror_vote)

        await send_bot_message(juror_bot,chat_id, juror_prompt)
        juror_responses.append(juror_prompt)

        juror_vote_clean = "".join(char for char in juror_vote if char not in string.punctuation).lower()


        if juror_vote_clean == "yes":
          juror_tally += 1
          print(str(juror_tally) + " added 1 to tally")
          #await send_bot_message(judge_bot, chat_id, f"{juror_identity} voted yes.")
        #elif juror_vote_clean == "no":
          #await send_bot_message(judge_bot, chat_id, f"{juror_identity} voted no.")
        #else :
          #await send_bot_message(judge_bot, chat_id, f"{juror_identity} did not vote.")
    
        if(juror < juror_amount - 1):
          await send_bot_message(judge_bot, chat_id, f"Thank you {juror_identity} for your deliberation. The next juror will now deliberate.")
        else :
          await send_bot_message(judge_bot, chat_id, f"Thank you {juror_identity} for your deliberation. The jury has finished deliberating. The judge will now give their final decision.")

    print("final tally" + str(juror_tally))

    judge_prompt = f"You are the judge who has been presiding over the case for {context.chat_data['main_user']}. The jury has deliberated and decided if the Plantiff has presented a justifiable reason to awarded World Peace Coin charity funds. The jury's decision is : {juror_tally} out of 11 jurors and here is the total juror descion : {juror_responses}. Based on the majority decision conclude as to which side won and make sure to include the final tally. Then, using the context from the Plaintiff : {plaintiff_remarks} and the Defendants remarks : {defendant_remarks} and the claims of the Client : {user_case} conclude by giving your official opinion on the case in the way that a Supreme Court Justice gives an opinion. However, thought you are free to have a contrary opinion with the ruling as this is your own personal take as a legal scholar on the matter, but you must NOT overrule the majority even if it goes agasint what you believe to be 'Justice'. Try to keep it brief to 150 words or less."

    judge_summary = generate_response(ai_model_judge, judge_system, judge_prompt)
    judge_remarks.append(judge_summary)

    await send_bot_message(judge_bot, chat_id, judge_summary)

    await send_bot_message(judge_bot, chat_id, "Court is now adjourned. Please type /startcourt to being a new case.")

    case_title = generate_response(ai_model_judge, judge_system, f"Read the case based on {judge_remarks} and {user_case}, then give it a very brief title, the title should be specific and capture what the case was about, do not speak in generalities. Try to keep it within 10 words or less.")

    # Determine the case decision


    case_decision_text = "Plaintiff Wins: " if juror_tally > 5 else "Defendant Wins: "
    if juror_tally > 5:
        case_decision_text += f"The Plaintiff has won the case with {juror_tally} out of 11 jurors voting in favor of the Plaintiff."
    else:
        juror_tally = 11 - juror_tally
        case_decision_text += f"The Defendant has won the case with {juror_tally} out of 11 jurors voting in favor of the Defendant."

    # Extracting plaintiff claims and evidence
    plaintiff_claims = context.chat_data['user_testimony']  # User testimony as claims
    plaintiff_evidence = context.chat_data['user_evidence']  # User evidence

    brief_summary = generate_response(ai_model_judge, judge_system, f"Use the {judge_remarks} and the {user_case} to create an extremely brief overview of the case. Try to keep it within 1-2 sentences.")

    # Generating a brief summary of the case
    # (You can use a similar generate_response call to create a brief summary or use judge_summary if it fits)

    # Formatting the final output
    final_decision = f"{context.chat_data['main_user']} vs. Fiji Court: {case_title}\n\n"
    final_decision += f"Claims: \"{plaintiff_claims}\"\n"
    final_decision += f"Evidence: \"{plaintiff_evidence}\"\n\n"
    final_decision += f"Abstract : {brief_summary}\n\n"
    final_decision += case_decision_text

    print(final_decision)

    case_name = context.chat_data['main_user'] + ":" + case_title + "-" + datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    file_name = case_name.replace(" ", "_")

    

    data.update({
    "case_name": case_name,
    "main_user": context.chat_data['main_user'],
    "user_testimony": context.chat_data['user_testimony'],
    "user_evidence": context.chat_data['user_evidence'],
    "court_date" : datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
    "plaintiff_remarks": plaintiff_remarks,
    "defendant_remarks": defendant_remarks,
    "judge_remarks": judge_remarks,
    "juror_identities": juror_identities,
    "juror_responses": juror_responses,
    "final_decision": final_decision
    })

    json_data = json.dumps(data, indent=4)

    file_path = os.path.join("case_files", file_name)

    with open(file_path, "w") as file:
      file.write(json_data)

    print(file_name)

    context.chat_data['court_state'] = 0
    context.chat_data['user_testimony'] = []
    context.chat_data['user_evidence'] = []

    plaintiff_remarks.clear()
    defendant_remarks.clear()
    judge_remarks.clear()
    juror_responses.clear()

    court_document = ""
    final_decision = ""



def main():
    # Adding handlers to each application
    judge_application.add_handler(CommandHandler('startcourt', start_court))
    judge_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message))
    judge_application.add_handler(CommandHandler('done', done_command))
    judge_application.add_handler(CommandHandler('cancel', cancel_command))


    # Run each application
    judge_application.run_polling()
    plaintiff_application.run_polling()
    defendant_application.run_polling()
    juror_application.run_polling()

if __name__ == "__main__":
    main()