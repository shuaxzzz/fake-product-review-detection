from flask import Blueprint, render_template, session, request
from datetime import datetime

product_bp = Blueprint("product", __name__)

# ================= PRODUCT DATABASE (TEMP - MOVE TO MONGODB LATER) =================
products = [
    {
        "id": "P1",
        "name": "The World Traveler Eyeshadow Palette",
        "image": "images/P1.png",
        "platform": "Shopee",
        "category": "Cosmetics",
        "brand": "Dazzle Me"
    },
    {
        "id": "P2",
        "name": "Double Ended Lip Gloss",
        "image": "images/P2.png",
        "platform": "Shopee",
        "category": "Cosmetics",
        "brand": "Mistine"
    },
    {
        "id": "P3",
        "name": "Uv Whitening 4 Beauty Benefits Perfect Last Refill",
        "image": "images/P3.png",
        "platform": "Shopee",
        "category": "Cosmetics",
        "brand": "Pixy"
    },
    {
        "id": "P4",
        "name": "Stayput Prime Set Continuous Setting Spray",
        "image": "images/P4.png",
        "platform": "Shopee",
        "category": "Cosmetics",
        "brand": "Sea Makeup"
    },
    {
        "id": "P5",
        "name": "2 In 1 Front Load Washing Machine Dryer",
        "image": "images/P5.png",
        "platform": "Shopee",
        "category": "Household Items",
        "brand": "Hisense"
    },
    {
        "id": "P6",
        "name": "Cool Tower Fan",
        "image": "images/P6.png",
        "platform": "Shopee",
        "category": "Household Items",
        "brand": "Dyson"
    },
    {
        "id": "P7",
        "name": "V8 Slim Fluffy Cordless Vacuum Cleaner",
        "image": "images/P7.png",
        "platform": "Shopee",
        "category": "Household Items",
        "brand": "Dyson"
    },
    {
        "id": "P8",
        "name": "HR2041 Everyday Blending W Ice Crushing Blender",
        "image": "images/P8.png",
        "platform": "Shopee",
        "category": "Household Items",
        "brand": "Philips"
    },
    {
        "id": "P9",
        "name": "NA110 12 In 1 Airfryer Oven",
        "image": "images/P9.png",
        "platform": "Shopee",
        "category": "Household Items",
        "brand": "Philips"
    },
    {
        "id": "P10",
        "name": "Perfectcare 7000 Series Steam Generator Iron ",
        "image": "images/P10.png",
        "platform": "Shopee",
        "category": "Household Items",
        "brand": "Philips"
    },
    {
        "id": "P11",
        "name": "MacBook Neo 13",
        "image": "images/P11.png",
        "platform": "Shopee",
        "category": "Electronics",
        "brand": "Apple"
    },
    {
        "id": "P12",
        "name": "Huawei Band 11 Smart Watch",
        "image": "images/P12.png",
        "platform": "Shopee",
        "category": "Electronics",
        "brand": "Huawei"
    },
    {
        "id": "P13",
        "name": "Huawei Matepad SE 11",
        "image": "images/P13.png",
        "platform": "Shopee",
        "category": "Electronics",
        "brand": "Huawei"
    },
    {
        "id": "P14",
        "name": "Huawei Nova 14 Pro Smartphone",
        "image": "images/P14.png",
        "platform": "Shopee",
        "category": "Electronics",
        "brand": "Huawei"
    },
    {
        "id": "P15",
        "name": "Redmi Note 15 Pro 5G Smartphone",
        "image": "images/P15.png",
        "platform": "Shopee",
        "category": "Electronics",
        "brand": "Redmi"
    },
    {
        "id": "P16",
        "name": "Redmi Note 15 Smartphone",
        "image": "images/P16.png",
        "platform": "Shopee",
        "category": "Electronics",
        "brand": "Redmi"
    },
    {
        "id": "P17",
        "name": "Redmi Watch 5",
        "image": "images/P17.png",
        "platform": "Shopee",
        "category": "Electronics",
        "brand": "Redmi"
    },
    {
        "id": "P18",
        "name": "Samsung Galaxy A17 5G Smartphone",
        "image": "images/P18.png",
        "platform": "Shopee",
        "category": "Electronics",
        "brand": "Samsung"
    },
    {
        "id": "P19",
        "name": "Samsung Galaxy A56 5G Smartphone",
        "image": "images/P19.png",
        "platform": "Shopee",
        "category": "Electronics",
        "brand": "Samsung"
    },
    {
        "id": "P20",
        "name": "Samsung Galaxy Buds Core",
        "image": "images/P20.png",
        "platform": "Shopee",
        "category": "Electronics",
        "brand": "Samsung"
    },
    {
        "id": "P21",
        "name": "Samsung Galaxy Fit 3",
        "image": "images/P21.png",
        "platform": "Shopee",
        "category": "Electronics",
        "brand": "Samsung"
    },
    {
        "id": "P22",
        "name": "Samsung Galaxy S25 Ultra",
        "image": "images/P22.png",
        "platform": "Shopee",
        "category": "Electronics",
        "brand": "Samsung"
    },
    {
        "id": "P23",
        "name": "Samsung Galaxy Tab S10 Lite Wifi",
        "image": "images/P23.png",
        "platform": "Shopee",
        "category": "Electronics",
        "brand": "Samsung"
    },
    {
        "id": "P24",
        "name": "Srs Xb100 Portable Wireless Speaker",
        "image": "images/P24.png",
        "platform": "Shopee",
        "category": "Electronics",
        "brand": "Sony"
    },
    {
        "id": "P25",
        "name": "WF C510 Truly Wireless Headphones",
        "image": "images/P25.png",
        "platform": "Shopee",
        "category": "Electronics",
        "brand": "Sony"
    },
    {
        "id": "P26",
        "name": "WH Ch520 Wireless Headphones",
        "image": "images/P26.png",
        "platform": "Shopee",
        "category": "Electronics",
        "brand": "Sony"
    },
    {
        "id": "P27",
        "name": "WI C100 Wireless In Ear Headphones",
        "image": "images/P27.png",
        "platform": "Shopee",
        "category": "Electronics",
        "brand": "Sony"
    },
    {
        "id": "P28",
        "name": "Ipad 11Th Generation Wi-Fi",
        "image": "images/P28.png",
        "platform": "Shopee",
        "category": "Electronics",
        "brand": "Apple"
    },
    {
        "id": "P29",
        "name": "Iphone 17",
        "image": "images/P29.png",
        "platform": "Shopee",
        "category": "Electronics",
        "brand": "Apple"
    },
    {
        "id": "P30",
        "name": "Iphone Finewoven Wallet With Magsafe",
        "image": "images/P30.png",
        "platform": "Shopee",
        "category": "Electronics",
        "brand": "Apple"
    },
    {
        "id": "P31",
        "name": "Apple Pencil Pro",
        "image": "images/P31.png",
        "platform": "Shopee",
        "category": "Electronics",
        "brand": "Apple"
    },
    {
        "id": "P32",
        "name": "Apple Watch Se 3 Gps",
        "image": "images/P32.png",
        "platform": "Shopee",
        "category": "Electronics",
        "brand": "Apple"
    },
    {
        "id": "P33",
        "name": "Xiaomi 17 Smartphone",
        "image": "images/P33.png",
        "platform": "Shopee",
        "category": "Electronics",
        "brand": "Xiaomi"
    },
    {
        "id": "P34",
        "name": "Iphone 16",
        "image": "images/P34.png",
        "platform": "Shopee",
        "category": "Electronics",
        "brand": "Apple"
    },
    {
        "id": "P35",
        "name": "Infallible Fresh Wear Cushion Foundation",
        "image": "images/P35.png",
        "platform": "Lazada",
        "category": "Cosmetics",
        "brand": "L'Oreal Paris"
    },
    {
        "id": "P36",
        "name": "Super Stay Lumi Matte Foundation",
        "image": "images/P36.png",
        "platform": "Lazada",
        "category": "Cosmetics",
        "brand": "Maybelline"
    },
    {
        "id": "P37",
        "name": "Super Stay Matte Ink Liquid Lipstick",
        "image": "images/P37.png",
        "platform": "Lazada",
        "category": "Cosmetics",
        "brand": "Maybelline"
    },
    {
        "id": "P38",
        "name": "4 In 1 Black Color Rainfall Shower Faucet Set",
        "image": "images/P38.png",
        "platform": "Lazada",
        "category": "Household Items",
        "brand": "Doboht"
    },
    {
        "id": "P39",
        "name": "Steam Oven Multifunctional Household Air Fryer Steam",
        "image": "images/P39.png",
        "platform": "Lazada",
        "category": "Household Items",
        "brand": "TJean"
    },
    {
        "id": "P40",
        "name": "Airpods Pro 3",
        "image": "images/P40.png",
        "platform": "Lazada",
        "category": "Electronics",
        "brand": "Apple"
    },
    {
        "id": "P41",
        "name": "20W Usb C Power Adapter",
        "image": "images/P41.png",
        "platform": "Lazada",
        "category": "Electronics",
        "brand": "Apple"
    },
    {
        "id": "P42",
        "name": "Macbook Air 13 Inch M5 2026",
        "image": "images/P42.png",
        "platform": "Lazada",
        "category": "Electronics",
        "brand": "Apple"
    },
    {
        "id": "P43",
        "name": "Huawei Freeclip 2",
        "image": "images/P43.png",
        "platform": "Lazada",
        "category": "Electronics",
        "brand": "Huawei"
    },
    {
        "id": "P44",
        "name": "Huawei Matepad Se 11 Tablet",
        "image": "images/P44.png",
        "platform": "Lazada",
        "category": "Electronics",
        "brand": "Huawei"
    },
    {
        "id": "P45",
        "name": "Huawei Nova 14 Series Smartphone",
        "image": "images/P45.png",
        "platform": "Lazada",
        "category": "Electronics",
        "brand": "Huawei"
    },
    {
        "id": "P46",
        "name": "Huawei Watch Fit 4 Series Smartwatch",
        "image": "images/P46.png",
        "platform": "Lazada",
        "category": "Electronics",
        "brand": "Huawei"
    },
   {
        "id": "P47",
        "name": "Redmi Buds 6 Play",
        "image": "images/P47.png",
        "platform": "Lazada",
        "category": "Electronics",
        "brand": "Redmi"
    },
    {
        "id": "P48",
        "name": "25W Power Adapter Usb C To C Without Cable",
        "image": "images/P48.png",
        "platform": "Lazada",
        "category": "Electronics",
        "brand": "Samsung"
    },
    {
        "id": "P49",
        "name": "Samsung Galaxy A07 5G Smartphone",
        "image": "images/P49.png",
        "platform": "Lazada",
        "category": "Electronics",
        "brand": "Samsung"
    },
    {
        "id": "P50",
        "name": "Samsung Galaxy A26 5G Smartphone",
        "image": "images/P50.png",
        "platform": "Lazada",
        "category": "Electronics",
        "brand": "Samsung"
    },
    {
        "id": "P51",
        "name": "Samsung Galaxy S25 Fe 5G Smartphone",
        "image": "images/P51.png",
        "platform": "Lazada",
        "category": "Electronics",
        "brand": "Samsung"
    },
    {
        "id": "P52",
        "name": "Linkbuds S Wireless Earphones",
        "image": "images/P52.png",
        "platform": "Lazada",
        "category": "Electronics",
        "brand": "Sony"
    },
    {
        "id": "P53",
        "name": "WF 1000Xm5 Wireless Earphones",
        "image": "images/P53.png",
        "platform": "Lazada",
        "category": "Electronics",
        "brand": "Sony"
    },
    {
        "id": "P54",
        "name": "WH Xb910N Wireless Bluetooth Noise Canceling Headphones",
        "image": "images/P54.png",
        "platform": "Lazada",
        "category": "Electronics",
        "brand": "Sony"
    },
    {
        "id": "P55",
        "name": "Zv 1F Vlog Camera",
        "image": "images/P55.png",
        "platform": "Lazada",
        "category": "Electronics",
        "brand": "Sony"
    },
    {
        "id": "P56",
        "name": "Xiaomi Power Bank 10000Mah",
        "image": "images/P56.png",
        "platform": "Lazada",
        "category": "Electronics",
        "brand": "Xiaomi"
    },
    
    {
        "id": "P57",
        "name": "Xiaomi Smart Band 10",
        "image": "images/P57.png",
        "platform": "Lazada",
        "category": "Electronics",
        "brand": "Xiaomi"
    },
    {
        "id": "P58",
        "name": "Iphone 17 Pro Max",
        "image": "images/P58.png",
        "platform": "Lazada",
        "category": "Electronics",
        "brand": "Apple"
    },
    {
        "id": "P59",
        "name": "Watch Se 3 Gps",
        "image": "images/P59.png",
        "platform": "Lazada",
        "category": "Electronics",
        "brand": "Apple"
    },
    {
    
        "id": "P60",
        "name": "Tv A 32 2026 High Definition Google Tv Smart Tv",
        "image": "images/P60.png",
        "platform": "Lazada",
        "category": "Electronics",
        "brand": "Xiaomi"
    },
    {
        "id": "P61",
        "name": "CX1520 Pedestal Fan",
        "image": "images/P61.png",
        "platform": "Shopee",
        "category": "Household Items",
        "brand": "Philips"
    },
    {
        "id": "P62",
        "name": "Formaldehyde Air Purifer",
        "image": "images/P62.png",
        "platform": "Shopee",
        "category": "Household Items",
        "brand": "Dyson"
    },
    {
        "id": "P63",
        "name": "Supersonic Nural Hair Dryer",
        "image": "images/P63.png",
        "platform": "Shopee",
        "category": "Household Items",
        "brand": "Dyson"
    },
    {
        "id": "P64",
        "name": "V12 Detect Slim Fluffy Cordless Vacuum",
        "image": "images/P64.png",
        "platform": "Shopee",
        "category": "Household Items",
        "brand": "Dyson"
    },
    {
        "id": "P65",
        "name": "Quickchef 7pcs Set",
        "image": "images/P65.png",
        "platform": "Shopee",
        "category": "Household Items",
        "brand": "Tefal"
    },
    {
        "id": "P66",
        "name": "Rice Mate Mini Fuzzy Logic Rice Cooker",
        "image": "images/P66.png",
        "platform": "Shopee",
        "category": "Household Items",
        "brand": "Tefal"
    },
    {
        "id": "P67",
        "name": "Duo Power 2-in-1 Steam Iron",
        "image": "images/P67.png",
        "platform": "Shopee",
        "category": "Household Items",
        "brand": "Tefal"
    },
    {
        "id": "P68",
        "name": "Ingenio Plus Wok Spatula",
        "image": "images/P68.png",
        "platform": "Shopee",
        "category": "Household Items",
        "brand": "Tefal"
    },
    {
        "id": "P69",
        "name": "43-75 inch 4K Smart TV",
        "image": "images/P69.png",
        "platform": "Shopee",
        "category": "Household Items",
        "brand": "Hisense"
    },
    {
        "id": "P70",
        "name": "520L 4 Door Inverter Refrigerator Black",
        "image": "images/P70.png",
        "platform": "Shopee",
        "category": "Household Items",
        "brand": "Hisense"
    },
    {
        "id": "P71",
        "name": "Standard Inverter Air Conditioner",
        "image": "images/P71.png",
        "platform": "Shopee",
        "category": "Household Items",
        "brand": "Hisense"
    },
    {
        "id": "P72",
        "name": "NI-317W Polished Iron",
        "image": "images/P72.png",
        "platform": "Shopee",
        "category": "Household Items",
        "brand": "Panasonic"
    },
    {
        "id": "P73",
        "name": "TK-CS200 Countertop Water Purifier",
        "image": "images/P73.png",
        "platform": "Shopee",
        "category": "Household Items",
        "brand": "Panasonic"
    },
    {
        "id": "P74",
        "name": "Electric Fan",
        "image": "images/P74.png",
        "platform": "Shopee",
        "category": "Household Items",
        "brand": "Panasonic"
    },
    {
        "id": "P75",
        "name": "Slow Cooker Ceramic Pot",
        "image": "images/P75.png",
        "platform": "Shopee",
        "category": "Household Items",
        "brand": "Panasonic"
    },
    {
        "id": "P76",
        "name": "Filter Free Airy Serum Skin Tint",
        "image": "images/P76.png",
        "platform": "Shopee",
        "category": "Cosmetics",
        "brand": "Pixy"
    },
    {
        "id": "P77",
        "name": "Instant Age Rewind Concealer",
        "image": "images/P77.png",
        "platform": "Shopee",
        "category": "Cosmetics",
        "brand": "Maybelline"
    },
    {
        "id": "P78",
        "name": "Super Stay Matte Ink Liquid Lipstick",
        "image": "images/P78.png",
        "platform": "Shopee",
        "category": "Cosmetics",
        "brand": "Maybelline"
    },
    {
        "id": "P79",
        "name": "Fit Me Matte Poreless Pressed Powder",
        "image": "images/P79.png",
        "platform": "Shopee",
        "category": "Cosmetics",
        "brand": "Maybelline"
    },
    {
        "id": "P80",
        "name": "Hypercurl Waterproof Mascara",
        "image": "images/P80.png",
        "platform": "Shopee",
        "category": "Cosmetics",
        "brand": "Maybelline"
    },
    {
        "id": "P81",
        "name": "Colorfit Cream Blush-Lightweight",
        "image": "images/P81.png",
        "platform": "Shopee",
        "category": "Cosmetics",
        "brand": "Wardah"
    },
    {
        "id": "P82",
        "name": "Colorfit Velvet Powder Foundation",
        "image": "images/P82.png",
        "platform": "Shopee",
        "category": "Cosmetics",
        "brand": "Wardah"
    },
    {
        "id": "P83",
        "name": "Colorfit Velvet Matte Lip Mousse",
        "image": "images/P83.png",
        "platform": "Shopee",
        "category": "Cosmetics",
        "brand": "Wardah"
    },
    {
        "id": "P84",
        "name": "Crystal Secret Foaming Cleanser",
        "image": "images/P84.png",
        "platform": "Shopee",
        "category": "Cosmetics",
        "brand": "Wardah"
    },
    {
        "id": "P85",
        "name": "BTF HD Invisible Powder",
        "image": "images/P85.png",
        "platform": "Shopee",
        "category": "Cosmetics",
        "brand": "Dazzle Me"
    },
    {
        "id": "P86",
        "name": "Get a Grip Makeup Setting Spray",
        "image": "images/P86.png",
        "platform": "Shopee",
        "category": "Cosmetics",
        "brand": "Dazzle Me"
    },
    {
        "id": "P87",
        "name": "Ink-Gloss Lip Tint 12H",
        "image": "images/P87.png",
        "platform": "Shopee",
        "category": "Cosmetics",
        "brand": "Dazzle Me"
    },
    {
        "id": "P88",
        "name": "Acne Blur And Setting Compact Loose Powder",
        "image": "images/P88.png",
        "platform": "Shopee",
        "category": "Cosmetics",
        "brand": "Sea Makeup"
    },
    {
        "id": "P89",
        "name": "Vibrant Flushed Liquid Blush",
        "image": "images/P89.png",
        "platform": "Shopee",
        "category": "Cosmetics",
        "brand": "Sea Makeup"
    },
    {
        "id": "P90",
        "name": "Lacquer Shake Lip Ink",
        "image": "images/P90.png",
        "platform": "Shopee",
        "category": "Cosmetics",
        "brand": "Sea Makeup"
    },
    {
        "id": "P91",
        "name": "Whitening High SPF Sunscreen",
        "image": "images/P91.png",
        "platform": "Shopee",
        "category": "Cosmetics",
        "brand": "Mistine"
    },
    {
        "id": "P92",
        "name": "Instant Age Rewind Concealer",
        "image": "images/P92.png",
        "platform": "Lazada",
        "category": "Cosmetics",
        "brand": "Maybelline"
    },
    {
        "id": "P93",
        "name": "Fit Me Compact Powder",
        "image": "images/P93.png",
        "platform": "Lazada",
        "category": "Cosmetics",
        "brand": "Maybelline"
    },
    {
        "id": "P94",
        "name": "Colorfit Ultralight Matte Lipstick",
        "image": "images/P94.png",
        "platform": "Lazada",
        "category": "Cosmetics",
        "brand": "Wardah"
    },
    {
        "id": "P95",
        "name": "Colorfit Cream Blush",
        "image": "images/P95.png",
        "platform": "Lazada",
        "category": "Cosmetics",
        "brand": "Wardah"
    },
    {
        "id": "P96",
        "name": "Colorfit Velvet Powder Foundation",
        "image": "images/P96.png",
        "platform": "Lazada",
        "category": "Cosmetics",
        "brand": "Wardah"
    },
    {
        "id": "P97",
        "name": "C Defense Vitamin C Face Mist",
        "image": "images/P97.png",
        "platform": "Lazada",
        "category": "Cosmetics",
        "brand": "Wardah"
    },
    {
        "id": "P98",
        "name": "Attack on Sun Sunscreen",
        "image": "images/P98.png",
        "platform": "Lazada",
        "category": "Cosmetics",
        "brand": "Dazzle Me"
    },
    {
        "id": "P99",
        "name": "Fruit Justice Lip Balm",
        "image": "images/P99.png",
        "platform": "Lazada",
        "category": "Cosmetics",
        "brand": "Dazzle Me"
    },
    {
        "id": "P100",
        "name": "Supore-Fine Skin Makeup Primer",
        "image": "images/P100.png",
        "platform": "Lazada",
        "category": "Cosmetics",
        "brand": "Dazzle Me"
    },
    {
        "id": "P101",
        "name": "Misty Matte Lip Cream",
        "image": "images/P101.png",
        "platform": "Lazada",
        "category": "Cosmetics",
        "brand": "Dazzle Me"
    },
    {
        "id": "P102",
        "name": "Radiance Booster Serum Spray Facial Oil",
        "image": "images/P102.png",
        "platform": "Lazada",
        "category": "Cosmetics",
        "brand": "Skintific"
    },
    {
        "id": "P103",
        "name": "Vitamin E Lip Serum",
        "image": "images/P103.png",
        "platform": "Lazada",
        "category": "Cosmetics",
        "brand": "Skintific"
    },
    {
        "id": "P104",
        "name": "Cover All Perfect Sunscreen Cushion",
        "image": "images/P104.png",
        "platform": "Lazada",
        "category": "Cosmetics",
        "brand": "Skintific"
    },
    {
        "id": "P105",
        "name": "Invisible Loose Powder",
        "image": "images/P105.png",
        "platform": "Lazada",
        "category": "Cosmetics",
        "brand": "Skintific"
    },
    {
        "id": "P106",
        "name": "Infallible 24H Tinted Serum Foundation",
        "image": "images/P106.png",
        "platform": "Lazada",
        "category": "Cosmetics",
        "brand": "L'Oreal Paris"
    },
    {
        "id": "P107",
        "name": "Color Riche Intense Volume Matte Lipstick",
        "image": "images/P107.png",
        "platform": "Lazada",
        "category": "Cosmetics",
        "brand": "L'Oreal Paris"
    },
    {
        "id": "P108",
        "name": "Revitalift Anti Aging Day Cream",
        "image": "images/P108.png",
        "platform": "Lazada",
        "category": "Cosmetics",
        "brand": "L'Oreal Paris"
    },
    {
        "id": "P109",
        "name": "High Speed Hair Dryer",
        "image": "images/P109.png",
        "platform": "Lazada",
        "category": "Household Items",
        "brand": "TJean"
    },
    {
        "id": "P110",
        "name": "2-in-1 Front Load Inverter Washer",
        "image": "images/P110.png",
        "platform": "Lazada",
        "category": "Household Items",
        "brand": "Hisense"
    },
    {
        "id": "P111",
        "name": "Inverter CLB Series Fast Cooling",
        "image": "images/P111.png",
        "platform": "Lazada",
        "category": "Household Items",
        "brand": "Hisense"
    },
    {
        "id": "P112",
        "name": "4K UHD Smart TV Voice Control",
        "image": "images/P112.png",
        "platform": "Lazada",
        "category": "Household Items",
        "brand": "Hisense"
    },
    {
        "id": "P113",
        "name": "2 Door Inverter Refrigerator 240L",
        "image": "images/P113.png",
        "platform": "Lazada",
        "category": "Household Items",
        "brand": "Hisense"
    },
    {
        "id": "P114",
        "name": "ES-CM3A 3-Blade Shaver",
        "image": "images/P114.png",
        "platform": "Lazada",
        "category": "Household Items",
        "brand": "Panasonic"
    },
    {
        "id": "P115",
        "name": "ES6850 Shaver Battery",
        "image": "images/P115.png",
        "platform": "Lazada",
        "category": "Household Items",
        "brand": "Panasonic"
    },
    {
        "id": "P116",
        "name": "EH-NE6M Ionity Hair Dryer",
        "image": "images/P116.png",
        "platform": "Lazada",
        "category": "Household Items",
        "brand": "Panasonic"
    },
    {
        "id": "P117",
        "name": "EH-ND37 Fast Dry Hair Dryer",
        "image": "images/P117.png",
        "platform": "Lazada",
        "category": "Household Items",
        "brand": "Panasonic"
    },
    {
        "id": "P118",
        "name": "Multi-Region Universal Power Adapter",
        "image": "images/P118.png",
        "platform": "Lazada",
        "category": "Household Items",
        "brand": "Philips"
    },
    {
        "id": "P119",
        "name": "CX1520 Pedestal Fan",
        "image": "images/P119.png",
        "platform": "Lazada",
        "category": "Household Items",
        "brand": "Philips"
    },
    {
        "id": "P120",
        "name": "Table Fan",
        "image": "images/P120.png",
        "platform": "Lazada",
        "category": "Household Items",
        "brand": "Philips"
    },
    {
        "id": "P121",
        "name": "Tower Fan 5000 Series",
        "image": "images/P121.png",
        "platform": "Lazada",
        "category": "Household Items",
        "brand": "Philips"
    }
]


# ================= PRODUCT PAGE =================
@product_bp.route("/products")
def product_page():

    return render_template(
        "detection.html",
        user=session.get("user"),
        products=products
    )

# ================= DETECTION PAGE =================
@product_bp.route("/detection")
def detection():
    return render_template(
        "detection.html",
        user=session.get("user"),
        products=products
    )

# ================= FILTER API (OPTIONAL FUTURE UPGRADE) =================
@product_bp.route("/api/products")
def get_products():

    platform = request.args.get("platform")
    category = request.args.get("category")
    brand = request.args.get("brand")

    filtered = products

    if platform and platform != "All":
        filtered = [p for p in filtered if p["platform"] == platform]

    if category and category != "All":
        filtered = [p for p in filtered if p["category"] == category]

    if brand and brand != "All":
        filtered = [p for p in filtered if p["brand"] == brand]

    return {"products": filtered}