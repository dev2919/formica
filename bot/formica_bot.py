import discord
import os
import json
from decouple import config



client = discord.Client()

form_color = 0xff8906
# define messages
welcome_title = "Welcome to Formica, the in-discord form service!"
welcome_msg = "It looks like you have a form to fill out. To do so, please react to this message with any emoji. Then, check your inbox!"
form_name = "Event Registration"


form_init_msg = "To start, type !start"


responses = []
form_started = False

def start_form():
    form_started = True
    global responses
    with open("dummy_questions.json", "r") as q:
        questions = json.load(q)
        q_count = len(questions)
    
    with open('dummy_responses.json', 'r') as r:
        responses = json.load(r)

    return questions, q_count


def get_question(questions, cur_index):
    cur_q_embed = discord.Embed(title = questions[cur_index]['question'], description = questions[cur_index]['description'], color = form_color)
    return cur_q_embed

def set_response(response, author, index):
    global responses
    # get the responses from the database
    # with open('dummy_responses.json', 'r') as r:
    #     responses = json.load(r)
    
    # test
    # print("retrieved responses: ", database_responses)
    # print("type: ", type(database_responses))
    # print(f"response: {response}, author: {author}, author id: {author.id}")

    # search database for the user
    try:
        target = next(user for user in responses if user['username'] == str(author) )
        # print("target: ", target)

        # get index
        target_index = responses.index(target)
        #print("found at index ", target_index)    

        #set response
        responses[target_index]['responses'].append(response)
        #print("set: ", responses)
    except:
        print("not found")
        # append to database
        responses.append({'username': str(author), 'user_id': str(author.id), 'responses': [response]})
        #print("appended: ", responses)

        target_index = len(responses) - 1
    
    return target_index

def end_form(questions, author_index):
    form_started = False
    global responses
    confirmation_embed = discord.Embed(title = 'Confirm your answers', description = 'React with ✅ to submit.\n If you need to edit your answers, go back and do so, then type !finished.', color = form_color)

    # print("responses: ", responses)
    # print("1st q: ", questions[0]['question'])
    # print("1st response: ", responses[author_index]['responses'][0])

    for item in range(len(questions)):
        confirmation_embed.add_field(name = questions[item]['question'], value = responses[author_index]['responses'][item], inline = False)
    
    return confirmation_embed

def submit_responses():
    global responses
    #write to the database
    with open('dummy_responses.json', 'w') as w:
        json.dump(responses, w)
    


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    #get_questions()

# listen for messages/commands
@client.event
async def on_message(message):
    msg = message.content

    #ignore, if the msg is from ourselves
    if message.author == client.user:
        return

    # listen for commands
    if msg.startswith('!formica'):
        #embed constructor
        welcome_embed = discord.Embed(title = welcome_title, description = welcome_msg, color = form_color)
        welcome_embed.add_field(name = "Form: ", value = form_name, inline = False)

        # send welcome message
        await message.channel.send(embed=welcome_embed)
    
    if msg.startswith('!start'):
        if form_started == False:
            cur_index = 0
            questions, q_count = start_form()
            
        

        while cur_index < q_count:
            #print(f"cur index: {cur_index}, total qs: {q_count}")

            # send the current question
            q_embed = get_question(questions, cur_index)
            await message.channel.send(embed=q_embed)

            # wait for response
            def check(m):
                # check that it's the right user and channel
                # later: check that we're on the right question or else the form restarts
                return m.author.id == message.author.id and m.channel == message.channel

            msg = await client.wait_for('message', check=check)

            # save response
            cur_response = msg.content
            author_index = set_response(msg.content, message.author, cur_index)

            # send feedback to user
            # await message.channel.send(f"Response received: {msg.content}")

            # update counters
            cur_index += 1
        
        #await message.channel.send("Questions completed")
        confirmation_embed = end_form(questions, author_index)
        await message.channel.send(embed=confirmation_embed)
        await message.add_reaction('✅')
        





# listen for reactions
@client.event
async def on_reaction_add(reaction, user):
    #ignore, if the msg is from ourselves
    # if user == client.user:
    #     return

    print("embed content: ", reaction.message.embeds)
    # grab the title of the embed msg that was reacted to
    message_title = reaction.message.embeds[0].title
    #message_title = reaction.message.embed.title
    print(f"Reaction to {message_title} detected")

    # check if the message was the welcome msg
    if message_title == welcome_title:
        # send the form instruction message to the user
        form_init = discord.Embed(title = form_name, description = form_init_msg, color = form_color)
        form_init.add_field(name = "Instructions: ", value = "Respond to my questions by typing a message like you normally would!\n You can edit your response by hovering on your message and clicking 'edit'.\n To see a list of available commands, type !help.", inline = False)

        await user.send(embed=form_init)

    if reaction.emoji == '✅' and message_title == 'Confirm your answers':
        submit_responses()
        await user.send("Responses have been submitted")



# run bot
BOT_TOKEN = config('TOKEN')
client.run(BOT_TOKEN)
