"""
A set of functions used for calculating and fetching an assortment of data.
"""

def real_title_case(text: str) -> str:
    """
    Like calling .title() except it wont capitalize words like `4v4`
    :param text: the text to turn title case
    """
    words = text.split()
    title_words = [word.title() if word[0].isalpha() else word for word in words]
    return ' '.join(title_words)


def get_player_dict(hypixel_data: dict) -> dict:
    """
    Checks if player key exits and returns data or empty dict
    :param hypixel_data: The hypixel data to the player of
    """
    if hypixel_data.get('player'):
        return hypixel_data['player']
    return {}


def get_most_played(hypixel_data_bedwars: dict) -> str:
    """
    Gets most played bedwars modes (solos, doubles, etc)
    :param hypixel_data_bedwars: Hypixel bedwars data from player > stats > Bedwars
    """
    modes_dict: dict = {
        'Solos': hypixel_data_bedwars.get('eight_one_games_played_bedwars', 0),
        'Doubles': hypixel_data_bedwars.get('eight_two_games_played_bedwars', 0),
        'Threes':  hypixel_data_bedwars.get('four_three_games_played_bedwars', 0),
        'Fours': hypixel_data_bedwars.get('four_four_games_played_bedwars', 0),
        '4v4': hypixel_data_bedwars.get('two_four_games_played_bedwars', 0)
    }
    if max(modes_dict.values()) == 0:
        return "N/A"
    return str(max(modes_dict, key=modes_dict.get))


def get_rank_info(hypixel_data: dict) -> dict:
    """
    Returns player's rank information including plus color
    :param hypixel_data: Hypixel data stemming from player key
    """
    name: str = hypixel_data.get('displayname')
    rank_info: dict = {
        'rank': hypixel_data.get('rank', 'NONE') if name != "Technoblade" else "TECHNO",
        'packageRank': hypixel_data.get('packageRank', 'NONE'),
        'newPackageRank': hypixel_data.get('newPackageRank', 'NONE'),
        'monthlyPackageRank': hypixel_data.get('monthlyPackageRank', 'NONE'),
        'rankPlusColor': hypixel_data.get('rankPlusColor', None) if name != "Technoblade" else "AQUA"
    }
    return rank_info


def xp_from_level(level: float) -> float | int:
    """
    Get the bedwars experience required for a given level
    :param level: Bedwars level
    """
    prestige, level = divmod(level, 100)
    xp = prestige * 487000
    xp_map = (0, 500, 1500, 3500, 7000)

    if level < 4:
        index = int(level)
        factor = xp_map[index]
        return int(xp + factor + (level - index) * (xp_map[index + 1] - factor))
    else:
        return int(xp + 7000 + (level - 4) * 5000)


def get_level(xp: int) -> float | int:
    """
    Get a player's precise bedwars level from their experience
    :param xp: Player's bedwars experience
    """
    level: int = 100 * (xp // 487000)  # prestige
    xp %= 487000  # exp this prestige
    xp_map: tuple = (0, 500, 1500, 3500, 7000)

    for index, value in enumerate(xp_map):
        if xp < value:
            factor: int = xp_map[index-1]
            return level + ((xp - factor) / (value - factor)) + (index - 1)
    return level + (xp - 7000) / 5000 + 4


def get_progress(hypixel_data_bedwars: dict) -> tuple[str, str, int]:
    """
    Get xp progress information: progress, target, and progress out of 10
    :param hypixel_data_bedwars: Bedwars data stemming from player > stats > Bedwars
    """
    bedwars_level: float | int = get_level(hypixel_data_bedwars.get('Experience', 0))

    remainder: int = int(str(int(bedwars_level) / 100).split(".")[-1])
    remainder_map: dict = {0: 500, 1: 1000, 2: 2000, 3: 3500}

    target: int = remainder_map.get(remainder, 5000)
    progress: float = float('.' + str(bedwars_level).split('.')[-1]) * target
    devide_by = target / 10
    progress_out_of_ten = round(progress / devide_by)

    return f'{int(progress):,}', f'{int(target):,}', progress_out_of_ten


# Suffixes used to approximate large numbers
suffixes = {
    10**60: 'NoDc', 10**57: 'OcDc', 10**54: 'SpDc', 10**51: 'SxDc', 10**48: 'QiDc', 10**45: 'QaDc',
    10**42: 'TDc', 10**39: 'DDc', 10**36: 'UDc', 10**33: 'Dc', 10**30: 'No', 10**27: 'Oc', 10**24: 'Sp',
    10**21: 'Sx', 10**18: 'Qi', 10**15: 'Qa', 10**12: 'T', 10**9: 'B', 10**6: 'M'
}


def add_suffixes(*args) -> list[str]:
    """
    Add suffixes to the end of large numbers to approximate them
    :param *args: A list of numbers to approximate
    """
    formatted_values: list = []
    for value in args:
        for num, suffix in suffixes.items():
            if value >= num:
                value: str = f"{value/num:,.1f}{suffix}"
                break
        else:
            value: str = f"{value:,}"
        formatted_values.append(value)
    return formatted_values


bedwars_modes_map: dict = {
    "overall": "",
    "solos": "eight_one_",
    "doubles": "eight_two_",
    "threes": "four_three_",
    "fours": "four_four_",
    "4v4": "two_four_"
}


def get_mode(mode: str) -> str:
    """
    Convert a mode (Solos, Doubles, etc) into hypixel format (eight_one_, eight_two_)
    If the mode doesnt exist, returns an empty string. Used to prefix stats
    eg: f'{mode}final_kills_bedwars'
    :param mode: The mode to convert
    """
    return bedwars_modes_map.get(mode.lower(), "")


def rround(number: float | int, ndigits: int=0) -> float | int:
    """
    Rounds a number. If the number is a whole number, it will be converted to an int
    :param number: Number to be round
    :param ndigits: Decimal place to round to
    """
    rounded: float = float(round(number, ndigits))
    if rounded.is_integer():
        rounded = int(rounded)
    return rounded


class BedwarsStats:
    """Wrapper for generic hypixel bedwars stats"""
    def __init__(self, hypixel_data: dict, strict_mode: str=None):
        """
        :param hypixel_data: the raw hypixel response json
        :param strict_mode: the mode to fetch stats for (solos, doubles, etc)
        if left as `None`, a dictionary of stats for every mode will be returned,
        otherwise just the stats for the specified mode will be returned
        """
        self._strict_mode = strict_mode
        self._hypixel_data = get_player_dict(hypixel_data)

        self._bedwars_data = self._hypixel_data.get('stats', {}).get('Bedwars', {})
        
        self.wins = self._get_mode_stats('wins_bedwars')
        self.losses = self._get_mode_stats('losses_bedwars')
        self.final_kills = self._get_mode_stats('final_kills_bedwars')
        self.final_deaths = self._get_mode_stats('final_deaths_bedwars')
        self.beds_broken = self._get_mode_stats('beds_broken_bedwars')
        self.beds_lost = self._get_mode_stats('beds_lost_bedwars')
        self.kills = self._get_mode_stats('kills_bedwars')
        self.deaths = self._get_mode_stats('deaths_bedwars')

        self.games_played = self._get_mode_stats('games_played_bedwars')
        self.most_played = get_most_played(self._bedwars_data)

        self.experience = self._bedwars_data.get('Experience', 0)
        self.progress = get_progress(self._bedwars_data)
        self.level = get_level(self.experience)

        self.items_purchased = self._get_mode_stats('items_purchased_bedwars')
        self.tools_purchased = self._get_mode_stats('permanent_items_purchased_bedwars')

        self.resources_collected = self._get_mode_stats('resources_collected_bedwars')
        self.iron_collected = self._get_mode_stats('iron_resources_collected_bedwars')
        self.gold_collected = self._get_mode_stats('gold_resources_collected_bedwars')
        self.diamonds_collected = self._get_mode_stats('diamond_resources_collected_bedwars')
        self.emeralds_collected = self._get_mode_stats('emerald_resources_collected_bedwars')

        self.winstreak = self._get_mode_stats('winstreak')
        if self.winstreak is not None:
            self.winstreak_str = f'{self.winstreak:,}'
        else:
            self.winstreak_str = 'API Off'


    def _get_mode_stats(self, key: str, default=0) -> dict | int:
        if self._strict_mode is None:
            mode_stats = {}
            for mode, prefix in bedwars_modes_map.items():
                mode_stats[mode] = self._bedwars_data.get(f'{prefix}{key}', default)
            return mode_stats

        prefix = bedwars_modes_map.get(self._strict_mode.lower())
        return self._bedwars_data.get(f'{prefix}{key}', default)
