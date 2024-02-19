"""### **1.2 Constants**"""
USER_AGENT = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
}

HEADERS = {
    'authority': 'api.sofascore.com',
    'accept': '*/*',
    'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
    'cache-control': 'max-age=0',
    'if-none-match': 'W/"0839132050"',
    'origin': 'https://www.sofascore.com',
    'referer': 'https://www.sofascore.com/',
    'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'If-Modified-Since' : 'Tue, 13 Feb 2024 00:00:00 GMT'
}

TEAM_NAMES_MAP = {
      # This list is not exhaustive and may need to be updated
        'epl' : {
            'Brighton & Hove Albion' : 'Brighton',
            'Luton Town' : 'Luton',
            'Tottenham Hotspur' : 'Tottenham',
            'West Ham United' : 'West Ham',
            'Wolverhampton' : 'Wolverhampton Wanderers',
            'Leeds United' : 'Leeds',
            'Leicester City': 'Leicester',
            'Norwich City'  : 'Norwich',
            'Cardiff City'  : 'Cardiff',
            'Huddersfield Town'  : 'Huddersfield',
            'Swansea City'  : 'Swansea',
            'Stoke City'  : 'Stoke',
            'Hull City' : 'Hull',
            "Parma" : "Parma Calcio 1913"
        },
        'bundesliga': {
            "Bayer 04 Leverkusen" : "Bayer Leverkusen",
            "RB Leipzig" : "RasenBallsport Leipzig",
            "SV Werder Bremen" : "Werder Bremen",
            "SC Freiburg" : "Freiburg",
            "TSG Hoffenheim" : "Hoffenheim",
            "VfL Wolfsburg" : "Wolfsburg",
            "VfL Bochum 1848" : "Bochum",
            "1. FC Heidenheim" : "FC Heidenheim",
            "1. FSV Mainz 05" : "Mainz 05",
            "1. FC Köln": "FC Cologne",
            "1. FC Union Berlin": "Union Berlin",
            "FC Augsburg": "Augsburg",
            "FC Bayern München": "Bayern Munich",
            "FC Ingolstadt 04": "Ingolstadt",
            "Borussia M'gladbach": "Borussia M.Gladbach",
            "Hertha BSC": "Hertha Berlin",
            "FC Schalke 04" : "Schalke 04",
            "SpVgg Greuther Fürth": "Greuther Fuerth",
            "SC Paderborn 07": "Paderborn",
            "Fortuna Düsseldorf" : "Fortuna Duesseldorf",
            "1. FC Nürnberg": "Nuernberg",
            "Darmstadt 98": "Darmstadt",
        },
        'serie_a': {
            "Milan" : 'AC Milan',
            "Hellas Verona" : "Verona",
            "SPAL" : "SPAL 2013",
            "ChievoVerona": "Chievo"
        },
        'laliga': {
            'Girona FC' : 'Girona', 
            'Atlético Madrid' : 'Atletico Madrid', 
            'Deportivo Alavés' : 'Alaves',
            'Cádiz' : 'Cadiz', 
            'Almería' : 'Almeria'
        },
        'ligue_1': {
            'Paris Saint-Germain' : 'Paris Saint Germain',
            'Stade Brestois' : 'Brest',
            'Stade Rennais': 'Rennes',
            'AS Monaco': 'Monaco',
            'Olympique de Marseille': 'Marseille',
            'Saint-Étienne' : 'Saint-Etienne',
            'RC Strasbourg' : 'Strasbourg',
            'Stade de Reims' : 'Reims',
            'Olympique Lyonnais': 'Lyon',
        },
      }