import os
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel
import ast
import re
import html
import json


load_dotenv()

# --- Gemini API Configuration ---
file_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

try:
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        project_id = data['project_id']
        location = 'us-central1'
except FileNotFoundError:
    print(f"File not found: {file_path}")

model_name = os.getenv("GEMINI_MODEL")

# Initialize Vertex AI SDK using the loaded config
vertexai.init(project=project_id, location=location)
gemini_model = GenerativeModel(model_name=model_name)

# Azure TTS Setup (Key + Endpoint)
speech_key = os.getenv("AZURE_TTS_KEY")
endpoint = os.getenv("AZURE_TTS_ENDPOINT")



def summarize_text_with_gemini(text):
    """
    Summarize text into a 2-5 minute podcast script.
    """
    prompt = """
    Summarize the following text into a natural, engaging audio script lasting 2 to 5 minutes.
    Use conversational tone, keep key ideas, and structure it like a short audio episode.
    Aim for 400-600 words. Output should be free of any formating like '''pyhton or any unnecessary symbols or asterisks.
    Output two python lists containing strings for two speakers of the podcast. The strings should be sequential ie after the first sentence of speaker 1,
    the sentence of speaker 2 should start. Text:
    """ + text

    response = gemini_model.generate_content(prompt).text.strip()

    print(response)

    response = re.sub(r'^```(?:python|py)?\s*', '', response, flags=re.IGNORECASE)
    response = re.sub(r'```.*$', '', response, flags=re.DOTALL)
    response = response.strip()

    lists_found = []
    i = 0
    while i < len(response):
        if response[i] == '[':
            bracket_depth = 0
            start = i
            for j in range(i, len(response)):
                if response[j] == '[':
                    bracket_depth += 1
                elif response[j] == ']':
                    bracket_depth -= 1

                if bracket_depth == 0:
                    list_str = response[start:j+1]
                    try:
                        parsed = ast.literal_eval(list_str)
                        if isinstance(parsed, list) and all(isinstance(item, str) for item in parsed):
                            lists_found.append(parsed)
                        break
                    except Exception:
                        break 
            i = j + 1
        else:
            i += 1

    if len(lists_found) < 2:
        raise ValueError(f"Expected two string lists, found {len(lists_found)}: {lists_found}")

    return lists_found[0], lists_found[1]


def generate_ssml_for_two_speakers(speaker1_lines, speaker2_lines):

    speaker1_voice="en-US-AvaNeural"
    speaker2_voice="en-US-AndrewNeural"
    pause="400ms"

    ssml_parts = ['<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">']
    
    for i in range(max(len(speaker1_lines), len(speaker2_lines))):
        if i < len(speaker1_lines):
            text = html.escape(speaker1_lines[i])
            ssml_parts.append(f'  <voice name="{speaker1_voice}">')
            ssml_parts.append(f'    {text}')
            if i < len(speaker1_lines) - 1 or i < len(speaker2_lines):  # If more lines follow
                ssml_parts.append(f'    <break time="{pause}" />')
            ssml_parts.append('  </voice>')

        if i < len(speaker2_lines):
            text = html.escape(speaker2_lines[i])
            ssml_parts.append(f'  <voice name="{speaker2_voice}">')
            ssml_parts.append(f'    {text}')
            if i < len(speaker2_lines) - 1 or i < len(speaker1_lines) - 1:  # If more lines follow
                ssml_parts.append(f'    <break time="{pause}" />')
            ssml_parts.append('  </voice>')

    ssml_parts.append('</speak>')
    return '\n'.join(ssml_parts)


def text_to_speech(text, output_file):
    """Convert text to speech using Azure TTS and save as MP3."""

    # Create speech configuration
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, endpoint=endpoint)

    # Set the audio output file
    audio_config = speechsdk.audio.AudioOutputConfig(filename=output_file)

    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    result = synthesizer.speak_ssml_async(text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("Speech synthesized and saved to conversation_output.mp3")
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print(f"Speech synthesis canceled: {cancellation_details.reason}")
        if cancellation_details.error_details:
            print(f"Error details: {cancellation_details.error_details}")


def create_audio(input_file, output_audio):
    print("Summarizing with Gemini...")
    summarized_text_sp1, summarized_text_sp2 = summarize_text_with_gemini(input_file)
    
    ssml = generate_ssml_for_two_speakers(summarized_text_sp1, summarized_text_sp2)

    text_to_speech(ssml, output_audio)
    print("Podcast generated successfully!")


def main():
    file = '''
A Historical Journey Through the South of France Introduction The South of France, renowned for its picturesque landscapes, charming villages, and stunning coastline, is also steeped in history. From ancient Roman ruins to medieval fortresses and Renaissance architecture, this region oﬀers a fascinating glimpse into the past. This guide will take you through the histories of major cities, famous historical sites, and other points of interest to help you plan an enriching and unforgettable trip. Marseille: The Oldest City in France Marseille, founded by Greek sailors around 600 BC, is the oldest city in France. Its strategic location on the Mediterranean coast made it a vital trading port throughout history. The city's rich cultural heritage is reflected in its diverse architecture and vibrant atmosphere. Key Historical Sites in Marseille •Old Port (Vieux-Port): The heart of Marseille, the Old Port has been a bustling harbor for over 2,600 years. Today, it is a lively area filled with cafes, restaurants, and markets. •Basilica of Notre-Dame de la Garde: This iconic basilica, perched on a hill overlooking the city, oﬀers panoramic views of Marseille and the Mediterranean Sea. Built in the 19th century, it is a symbol of the city's maritime heritage. •Fort Saint-Jean: Constructed in the 17th century, this fort guards the entrance to the Old Port. It now houses part of the Museum of European and Mediterranean Civilizations (MuCEM). •Le Panier: The oldest district in Marseille, Le Panier is a maze of narrow streets, colorful buildings, and historic landmarks. It's a great place to explore the city's past and enjoy its vibrant culture. •Château d'If: Commissioned by King Francis I in 1524, this fortress on the Île d'If became famous as a prison and was immortalized in Alexandre Dumas' novel "The Count of Monte Cristo"1. •La Marseillaise: Marseille played a significant role during the French Revolution, and the city's volunteers composed the national anthem of France, "La Marseillaise"2. Nice: The Jewel of the French Riviera Nice, located on the French Riviera, has been a popular destination for centuries. Its history dates back to the ancient Greeks, who founded the city around 350 BC. Nice later became a Roman colony and has since evolved into a glamorous resort town. Key Historical Sites in Nice •Castle Hill (Colline du Château): This hilltop park oﬀers stunning views of Nice and the Mediterranean. It was once the site of a medieval castle, which was destroyed in the 18th century. •Promenade des Anglais: This famous seaside promenade was built in the 19th century and named after the English aristocrats who frequented Nice. It's perfect for a leisurely stroll along the coast. •Old Town (Vieux Nice): The historic center of Nice is a labyrinth of narrow streets, baroque churches, and bustling markets. Don't miss the Cours Saleya market, where you can find fresh produce, flowers, and local delicacies. •Russian Orthodox Cathedral: Built in the early 20th century, this stunning cathedral reflects the influence of Russian aristocrats who vacationed in Nice. •Cimiez: An ancient Roman settlement, Cimiez is home to the ruins of a Roman amphitheater and baths, as well as the Monastery of Cimiez, which oﬀers beautiful gardens and a museum dedicated to the painter Henri Matisse3. •Carnival of Nice: One of the most famous carnivals in France, the Carnival of Nice dates back to 1873 and features elaborate parades, floats, and flower battles4. Avignon: The City of Popes Avignon, located on the banks of the Rhône River, is best known for its role as the seat of the papacy in the 14th century. The city was home to seven popes during this period, leaving a lasting legacy of impressive architecture and cultural heritage. Key Historical Sites in Avignon •Palais des Papes: This massive Gothic palace was the residence of the popes during their stay in Avignon. It is one of the largest and most important medieval Gothic buildings in Europe. •Pont Saint-Bénézet (Pont d'Avignon): This famous bridge, immortalized in the song "Sur le Pont d'Avignon," was built in the 12th century. Although only a few arches remain, it is a UNESCO World Heritage site. •Avignon Cathedral: Located next to the Palais des Papes, this Romanesque cathedral dates back to the 12th century and features a gilded statue of the Virgin Mary. •Place de l'Horloge: The main square in Avignon, this lively area is surrounded by cafes, restaurants, and historic buildings, including the 19th-century town hall and opera house. •Rocher des Doms: This rocky outcrop oﬀers panoramic views of the Rhône River and the surrounding countryside. It has been a strategic site since prehistoric times and now features beautiful gardens5. •Avignon Festival: Established in 1947, the Avignon Festival is one of the most important contemporary performing arts events in the world, attracting artists and audiences from around the globe6. Nîmes: The Rome of France Nîmes, often referred to as the "Rome of France," boasts some of the best-preserved Roman architecture in the country. The city's history dates back to the Roman Empire, when it was an important settlement in the province of Gallia Narbonensis. Key Historical Sites in Nîmes •Arena of Nîmes: This Roman amphitheater, built in the 1st century AD, is one of the best-preserved in the world. It still hosts events, including concerts and bullfights. •Maison Carrée: A beautifully preserved Roman temple, the Maison Carrée dates back to the 1st century BC. It is one of the best examples of classical Roman architecture. •Pont du Gard: Located just outside Nîmes, this ancient Roman aqueduct is a UNESCO World Heritage site. It was built in the 1st century AD to transport water to the city. •Jardins de la Fontaine: These 18th-century gardens are built around the ruins of a Roman sanctuary. They oﬀer a peaceful retreat with beautiful fountains, statues, and shaded pathways. •Tour Magne: This ancient Roman tower, part of the city's original fortifications, oﬀers panoramic views of Nîmes and the surrounding area7. •Temple of Diana: Located in the Jardins de la Fontaine, this Roman temple's exact purpose remains a mystery, but it is believed to have been a library or a place of worship8. Carcassonne: A Medieval Fortress Carcassonne is a fortified city in the Languedoc region, known for its well-preserved medieval architecture. The city's history dates back to the Roman period, but it is best known for its role in the medieval period as a stronghold during the Albigensian Crusade. Key Historical Sites in Carcassonne •Cité de Carcassonne: This medieval fortress is a UNESCO World Heritage site and one of the most impressive examples of medieval architecture in Europe. It features double walls, 52 towers, and a castle. •Basilica of Saints Nazarius and Celsus: This Gothic-Romanesque basilica, located within the fortress, dates back to the 11th century. It is known for its beautiful stained glass windows. •Château Comtal: This castle, located within the Cité, oﬀers guided tours that provide insight into the history and architecture of Carcassonne. •Pont Vieux: This 14th-century bridge connects the medieval Cité with the lower town. It oﬀers stunning views of the fortress and the surrounding countryside. •Inquisition Tower: One of the Roman towers in Carcassonne, it was used during the Medieval Inquisition to imprison and torture suspected heretics9. •Hoardings: Carcassonne was the first fortress to use wooden hoardings during sieges, allowing defenders to shoot arrows and drop projectiles on attackers below10. Toulouse: The Pink City Toulouse, known as "La Ville Rose" (The Pink City) due to its distinctive terracotta buildings, is a vibrant city with a rich history. It was an important center during the Roman period and later became a hub of the aerospace industry. Key Historical Sites in Toulouse •Basilica of Saint-Sernin: This Romanesque basilica, built between the 11th and 13th centuries, is a UNESCO World Heritage site. It is one of the largest and best-preserved Romanesque churches in Europe. •Capitole de Toulouse: The city's town hall and theater, the Capitole, is an impressive building with a neoclassical facade. It has been the seat of municipal power since the 12th century. •Jacobins Convent: This Gothic convent, founded in the 13th century, is known for its beautiful cloister and the relics of Saint Thomas Aquinas. •Pont Neuf: Despite its name, which means "New Bridge," this is the oldest bridge in Toulouse. It was completed in the 17th century and oﬀers picturesque views of the Garonne River. •Canal du Midi: A UNESCO World Heritage site, this canal connects the Garonne River to the Mediterranean Sea and was a major engineering feat of the 17th century. •Aeroscopia Museum: Reflecting Toulouse's role as a center of the aerospace industry, this museum showcases the history of aviation with exhibits including the Concorde and Airbus aircraft. Arles: A Roman Treasure Arles, located on the banks of the Rhône River, is renowned for its Roman and Romanesque monuments. The city was an important Roman settlement and later became a center of Christian pilgrimage. Key Historical Sites in Arles •Arles Amphitheatre: This Roman amphitheater, built in the 1st century AD, is still used for events such as bullfights and concerts. It is one of the best-preserved Roman structures in France. •Church of St. Trophime: This Romanesque church, built in the 12th century, is known for its stunning portal and cloister. It was an important stop on the pilgrimage route to Santiago de Compostela. •Alyscamps: This ancient Roman necropolis, located just outside the city walls, was a major burial site in antiquity. It features a long avenue lined with sarcophagi. •Thermes de Constantin: These Roman baths, built in the 4th century AD, are a testament to the city's importance during the Roman period. •Van Gogh's Influence: Arles is also famous for its association with Vincent van Gogh, who created over 300 works of art during his time in the city. The Van Gogh Foundation in Arles celebrates his legacy. •Cryptoporticus: An underground gallery built by the Romans in the 1st century BC, it served as a foundation for the Forum and is one of the few remaining examples of such structures. Aix-en-Provence: A City of Art and Culture Aix-en-Provence, founded by the Romans in 123 BC, is known for its elegant architecture, vibrant cultural scene, and association with the painter Paul Cézanne. The city's rich history is reflected in its beautiful buildings and lively atmosphere. Key Historical Sites in Aix-en-Provence •Cours Mirabeau: This grand boulevard, lined with plane trees, cafes, and fountains, is the heart of Aix-en-Provence. It is a great place to soak up the city's atmosphere. •Saint-Sauveur Cathedral: This cathedral, built between the 5th and 17th centuries, features a mix of architectural styles, including Romanesque, Gothic, and Baroque. It is known for its beautiful cloister and triptych by Nicolas Froment. •Hôtel de Ville: The town hall of Aix-en-Provence, built in the 17th century, is an elegant building with a beautiful clock tower and an ornate facade. The square in front of the Hôtel de Ville is a lively spot, often hosting markets and events. •Atelier Cézanne: The studio of Paul Cézanne, one of the most famous painters associated with Aix-en-Provence, is preserved as a museum. Visitors can see where Cézanne created many of his masterpieces and gain insight into his artistic process. •Thermal Springs: Aix-en-Provence was originally founded as a Roman spa town due to its thermal springs, which are still in use today at the Thermes Sextius. •Festival d'Aix-en-Provence: An annual opera festival held in July, it is one of the most prestigious opera festivals in Europe. Montpellier: A University City with Medieval Charm Montpellier, founded in the 10th century, is known for its prestigious university and vibrant cultural scene. The city has a rich history, with a blend of medieval, Renaissance, and modern architecture. Key Historical Sites in Montpellier •Place de la Comédie: The central square of Montpellier, this bustling area is surrounded by cafes, shops, and the impressive Opéra Comédie. It is a great place to start exploring the city. •Saint-Pierre Cathedral: This Gothic cathedral, built in the 14th century, is known for its imposing facade and twin towers. It is the seat of the Archdiocese of Montpellier. •Promenade du Peyrou: This 17th-century promenade oﬀers stunning views of the city and features the Arc de Triomphe and the Château d'Eau, a beautiful water tower. •Musée Fabre: One of the most important art museums in France, the Musée Fabre houses an extensive collection of European paintings, sculptures, and decorative arts. •University of Montpellier: Founded in 1289, it is one of the oldest universities in the world and has been a center of learning and culture for centuries. •Jardin des Plantes: Established in 1593, it is the oldest botanical garden in France and was created for the study of medicinal plants. Perpignan: A Blend of French and Catalan Cultures Perpignan, located near the Spanish border, has a unique blend of French and Catalan influences. The city was once the capital of the Kingdom of Majorca and has a rich history reflected in its architecture and culture. Key Historical Sites in Perpignan •Palace of the Kings of Majorca: This impressive fortress, built in the 13th century, was the residence of the Kings of Majorca. It oﬀers panoramic views of the city and the surrounding countryside. •Perpignan Cathedral: Also known as the Cathedral of Saint John the Baptist, this Gothic cathedral was built in the 14th century and features a beautiful cloister and bell tower. •Castillet: This iconic red-brick gatehouse, built in the 14th century, is a symbol of Perpignan. It now houses the Casa Pairal Museum, which showcases the history and culture of the region. •Loge de Mer: This historic building, originally a maritime trading exchange, dates back to the 14th century. It is located in the heart of the old town and is a testament to Perpignan's rich mercantile history. •Campo Santo: One of the largest and oldest cloister cemeteries in France, dating back to the 14th century. •Festival de Perpignan: An annual photojournalism festival, Visa pour l'Image, held in Perpignan, attracts photographers and journalists from around the world. Conclusion The South of France oﬀers a rich tapestry of history, culture, and architecture that is sure to captivate any traveler. From the ancient Roman ruins of Nîmes and Arles to the medieval fortresses of Carcassonne and Avignon, each city and town has its own unique story to tell. Whether you're exploring the vibrant streets of Marseille, the elegant boulevards of Aix-en-Provence, or the charming squares of Montpellier, you'll find a wealth of historical treasures waiting to be discovered. Use this guide to plan your journey through the South of France and immerse yourself in the fascinating history of this beautiful region.
{'key_insights': '["The South of France is rich in history, featuring Roman ruins, medieval fortresses, and Renaissance architecture.", "Marseille, founded around 600 BC, is the oldest city in France and a historic trading port.", "Nice, a popular destination for centuries, was founded by ancient Greeks and later became a Roman colony.", "Avignon served as the seat of the papacy in the 14th century, leaving a legacy of Gothic architecture.", "Nîmes is renowned for its well-preserved Roman architecture, earning it the nickname \'Rome of France\'."]', 'did_you_know': "['Marseille is the oldest city in France, founded by Greek sailors around 600 BC.', 'The Promenade des Anglais in Nice was named after the English aristocrats who frequented the city.', 'Carcassonne was the first fortress to use wooden hoardings during sieges.']", 'counterpoints': '[\n"The text focuses heavily on historical sites and architecture, potentially neglecting other aspects of the South of France that might appeal to travelers, such as its natural beauty, culinary scene, or modern cultural offerings.",\n"While the text highlights the historical significance of various cities, it might oversimplify or generalize the complex historical narratives of each location, potentially missing nuanced interpretations or alternative historical perspectives.",\n"The guide is presented as a planning tool for a trip, but it doesn\'t offer practical advice on logistics like transportation, accommodation, or best times to visit, which are crucial for trip planning."\n]'}
'''
    audio_loc = '/content/sample_data/output.mp3'
    create_audio(file, audio_loc)

if __name__ == "__main__":
    main()