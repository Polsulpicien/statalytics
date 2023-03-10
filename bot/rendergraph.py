import os
import json
import random
from io import BytesIO
import requests
from PIL import Image, ImageDraw, ImageFont
from custombackground import background
from rendername import rank_color

def rendergraph(name, uuid):
    # Get api key
    with open(f'{os.getcwd()}/database/apikeys.json', 'r') as keyfile:
        allkeys = json.load(keyfile)['keys']
    key = random.choice(list(allkeys))

    response = requests.get(f"https://api.hypixel.net/player?key={allkeys[key]}&uuid={uuid}", timeout=10)
    hypixel_data = response.json()

    solos = hypixel_data.get('player', {}).get('stats', {}).get('Bedwars', {}).get('eight_one_games_played_bedwars', 1)
    doubles = hypixel_data.get('player', {}).get('stats', {}).get('Bedwars', {}).get('eight_two_games_played_bedwars', 1)
    threes = hypixel_data.get('player', {}).get('stats', {}).get('Bedwars', {}).get('four_three_games_played_bedwars', 1)
    fours = hypixel_data.get('player', {}).get('stats', {}).get('Bedwars', {}).get('four_four_games_played_bedwars', 1)

    rank = hypixel_data['player'].get('rank', 'NONE')
    package_rank = hypixel_data['player'].get('packageRank', 'NONE')
    new_package_rank = hypixel_data['player'].get('newPackageRank', 'NONE')
    monthly_package_rank = hypixel_data['player'].get('monthlyPackageRank', 'NONE')
    rank_plus_color = hypixel_data['player'].get('rankPlusColor', None)
    player_rank = {
        'rank': rank,
        'packageRank': package_rank,
        'newPackageRank': new_package_rank,
        'monthlyPackageRank': monthly_package_rank,
        'rankPlusColor': rank_plus_color
    }

    rankcolor = rank_color(player_rank)

    # Get ratio
    numbers = [int(solos), int(doubles), int(threes), int(fours)]
    total = sum(numbers)
    ratios = [num / total for num in numbers]

    color = (0, 0, 255, 127)


    # Define the coordinates for the bars
    positions = [(97, 354), (220, 354), (343, 354), (466, 354)]

    # Open Images
    image_location = background(path=f'{os.getcwd()}/assets/graph', uuid=uuid, default='base')
    base_image = Image.open(image_location)
    base_image = base_image.convert("RGBA")

    bar_graph = Image.new('RGBA', (640, 420), (0, 0, 0, 0))
    draw = ImageDraw.Draw(bar_graph)

    # Draw the bars
    if max(ratios) * 500 > 250:
        difference = (max(ratios) * 500) - 250
        ratios = [value - (difference / 500) if value - (difference / 500) > 0 else 0 for value in ratios]


    for i, value in enumerate(ratios):
        height = 250 if value * 500 > 250 else value * 500
        draw.rectangle([positions[i], (positions[i][0] + 77, positions[i][1] - height)], fill=color)

    base_image = Image.alpha_composite(base_image, bar_graph)

    # Render text
    black = (0, 0, 0)
    white = (255, 255, 255)

    font = ImageFont.truetype(f'{os.getcwd()}/assets/minecraft.ttf', 20)
    player_y = 33
    player_txt = "'s Most Played Modes"

    totallength = draw.textlength(name, font=font) + draw.textlength(player_txt, font=font)
    startpoint = (640 - totallength) / 2

    draw = ImageDraw.Draw(base_image)

    draw.text((startpoint + 2, player_y + 2), name, fill=black, font=font)
    draw.text((startpoint, player_y), name, fill=rankcolor, font=font)

    startpoint += draw.textlength(name, font=font)

    draw.text((startpoint + 2, player_y + 2), player_txt, fill=black, font=font)
    draw.text((startpoint, player_y), player_txt, fill=white, font=font)

    # Render the titles
    overlay_image = Image.open(f'{os.getcwd()}/assets/graph/base_overlay.png')
    base_image.paste(overlay_image, (0, 0), overlay_image)

    # Return the image
    image_bytes = BytesIO()
    base_image.save(image_bytes, format='PNG')
    image_bytes.seek(0)

    return image_bytes
