"""Product SKU mapping used in converting product name to Newegg's (item_number, part_number) pair.

    product name: Name on sourced website (Bestbuy, Woocommerce).
    item_number: Item number for the product on Newegg website. This value is not currently being used.
    part_number: Newegg's SellerPartNumber when constructing a Newegg order and SKU displayed on dashboard page.
"""
PRODUCT_INFO = {
    "PulseLabz Guardian Series Gaming Chair - Black/Black": ("9SIAFG16RF1304", "G-BK"),
    "PulseLabz Guardian Series Office Gaming Chair - Black/Black": ("9SIAFG16RF1304", "G-BK"),
    "PulseLabz Guardian Series Gaming Chair - White/Black": ("9SIAFG16RF1303", "G-W"),
    "PulseLabz Guardian Series Gaming Chair - Blue/Black": ("9SIAFG16RF1302", "G-B"),
    "PulseLabz Guardian Series Gaming Chair - Red/Black": ("9SIAFG16RF1269", "G-R"),
    "PulseLabz Enforcer Series Gaming Chair - Black/Black": ("9SIAFG16RE9293", "E-BK"),
    "PulseLabz Enforcer Series Office Gaming Chair - Black/Black": ("9SIAFG16RE9293", "E-BK"),
    "PulseLabz Enforcer Series Gaming Chair - White/Black": ("9SIAFG16RE9292", "E-W"),
    "PulseLabz Enforcer Series Gaming Chair - Blue/Black": ("9SIAFG16RE9291", "E-B"),
    "PulseLabz Enforcer Series Gaming Chair - Red/Black": ("9SIAFG16RE9105", "E-R"),
    "PulseLabz Challenger Series Gaming Chair - Black/Black": ("9SIAFG16RE9054", "C-BK"),
    "PulseLabz Challenger Series Office Gaming Chair - Black/Black": ("9SIAFG16RE9054", "C-BK"),
    "PulseLabz Challenger Series Gaming Chair - White/Black": ("9SIAFG16RE8116", "C-W"),
    "PulseLabz Challenger Series Gaming Chair - Blue/Black": ("9SIAFG16RE8111", "C-B"),
    "PulseLabz Challenger Series Gaming Chair - Red/Black": ("9SIAFG16R80209", "C-R"),
    "PulseLabz Challenger Series Gaming Chair (W-trim) - White/Black": ('', "C-W"),
    "PulseLabz Challenger Series Gaming Chair - Green/Black": ('', "C-G"),
    "PulseLabz Challenger Series Gaming Chair - Orange/Black": ('', "C-O"),
    "Weapon Series Mouse Pad (X-Large) 90×40 cm": ("9SIAFG180E0723","MP-L"), # Woocommerce
    "Pulselabz Weapon Series XL Pro Gaming Mouse Pad (90x40cm) - Black": ("9SIAFG180E0723","MP-L"), # Bestbuy
    "Motion Series Dual Motor Table Frame – Black": ('9SIAFG17NX0510', "MG-Black"), # Woocommerce
    "MotionGrey Adjustable Electric Dual Motors Office Standing Desk - Black Frame": ('9SIAFG17NX0510', "MG-Black"), # Bestbuy
    "Motion Series Dual Motor Table Frame – White": ('9SIAFG17P44124', "MG1-White"), # Woocommerce
    "MotionGrey Adjustable Electric Dual Motors Office Standing Desk - White Frame": ('9SIAFG17P44124', "MG1-White"), # Bestbuy
    "Motion Series Dual Motor Table Frame – Grey": ('9SIAFG18GG9485', "MG-FRAME-GY"), # Woocommerce
    "MotionGrey Adjustable Electric Dual Motors Office Standing Desk - Grey Frame": ('9SIAFG18GG9485', "MG-FRAME-GY") # Bestbuy
}
