from datetime import datetime
from logging.config import listen
import speech_recognition as sr
import pyttsx3 
import webbrowser
import wikipedia
import wolframalpha
import ollama
import asyncio
import threading

# Speech engine initialisation
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id) # 0 = male, 1 = female
activationWord = 'computer' # Single word
 
# Configure browser
# Set the path
chrome_path = r"__________APPLICATION PATH___________"
webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_path))
 
# Wolfram Alpha client
appId = '______________________'
wolframClient = wolframalpha.Client(appId)
 
def speak(text, rate = 120):
    global stop_speech
    engine.setProperty('rate', rate)
    engine.say(text)
    engine.runAndWait()
    stop_speech = False  # Reset stop flag after speech is finished
 
def parseCommand():
    listener = sr.Recognizer()
    print('Listening for a command')
 
    with sr.Microphone() as source:
        listener.pause_threshold = 2
        input_speech = listener.listen(source)
 
    try: 
        print('Recognizing speech...')
        query = listener.recognize_google(input_speech, language='en_gb')
        print(f'The input speech was: {query}')

        if 'stop' in query.lower():  # Check for the stop word
            global stop_speech
            stop_speech = True

    except Exception as exception:
        print('I did not quite catch that')
        #speak('I did not quite catch that')
        print(exception)
        return 'None'
 
    return query
 
def search_wikipedia(query = ''):
    searchResults = wikipedia.search(query)
    if not searchResults:
        print('No wikipedia result')
        return 'No result received'
    try: 
        wikiPage = wikipedia.page(searchResults[0])
    except wikipedia.DisambiguationError as error:
        wikiPage = wikipedia.page(error.options[0])
    print(wikiPage.title)
    wikiSummary = str(wikiPage.summary)
    return wikiSummary
 
def listOrDict(var):
    if isinstance(var, list):
        return var[0]['plaintext']
    else:
        return var['plaintext']
 
def search_wolframAlpha(query = ''):
    response = wolframClient.query(query)
 
    # @success: Wolfram Alpha was able to resolve the query
    # @numpods: Number of results returned
    # pod: List of results. This can also contain subpods
    if response['@success'] == 'false':
        return 'Could not compute'
    
    # Query resolved
    else:
        result = ''
        # Question 
        pod0 = response['pod'][0]
        pod1 = response['pod'][1]
        # May contain the answer, has the highest confidence value
        # if it's primary, or has the title of result or definition, then it's the official result
        if (('result') in pod1['@title'].lower()) or (pod1.get('@primary', 'false') == 'true') or ('definition' in pod1['@title'].lower()):
            # Get the result
            result = listOrDict(pod1['subpod'])
            # Remove the bracketed section
            return result.split('(')[0]
        else: 
            question = listOrDict(pod0['subpod'])
            # Remove the bracketed section
            return question.split('(')[0]
            # Search wikipedia instead
            speak('Computation failed. Querying universal databank.')
            return search_wikipedia(question)
 
async def stbbrt_conversation(content):
    message = {'role': 'user', 'content': content}
    print(message)
    response = await ollama.AsyncClient().chat(model='_______', messages=[message])
    print(response['message']['content'])
    
    # Define a function to speak in a separate thread
    def speak_in_thread(text):
        global stop_speech
        stop_speech = False
        thread = threading.Thread(target=speak, args=(text,))
        thread.start()
        thread.join()  # Wait for the speech to finish or be interrupted

    # Speak the AI's response in a separate thread
    speak_in_thread(response['message']['content'])

    # Check for stop word during speech
    while not stop_speech:
        pass  # Keep listening for the stop word
 
# Global variable to track if speech should be stopped
stop_speech = False

# Main loop
if __name__ == '__main__':
    speak('All systems nominal.')
 
    while True:
        # Parse as a list
        query = parseCommand().lower().split()
 
        if query[0] == activationWord:
            query.pop(0)
 
            if query[0] == 'chat':
                speak("Chatting with AI")

                while True:
                    content = parseCommand()
                    if content == 'exit':
                        break
                    else:
                        asyncio.run(start_conversation(content))


            # List commands
            if query[0] == 'say':
                if 'hello' in query:
                    speak('Greetings, all.')
                else: 
                    query.pop(0) # Remove say
                    speech = ' '.join(query)
                    speak(speech)
 
            # Navigation
            if query[0] == 'go' and query[1] == 'to':
                speak('Opening...')
                query = ' '.join(query[2:])
                webbrowser.get('brave').open_new(query)
 
            # Wikipedia 
            if query[0] == 'wikipedia':
                query = ' '.join(query[1:])
                speak('Querying the universal databank.')
                speak(search_wikipedia(query))
                
            # Wolfram Alpha
            if query[0] == 'compute' or query[0] == 'computer' or query[0] == 'calculate' or query[0] == 'query':
                query = ' '.join(query[1:])
                speak('Computing')
                try: 
                    result = search_wolframAlpha(query)
                    speak(result)
                except:
                    speak('Unable to compute.')
 
            # Note taking
            if query[0] == 'log':
                speak('note recording.')
                newNote = parseCommand().lower()
                now = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
                with open('note_%s.txt' % now, 'w') as newFile:
                    newFile.write(newNote)
                speak('Note written')
 
            if query[0] == 'exit':
                speak('Goodbye')
                break
