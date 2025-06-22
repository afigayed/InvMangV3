import streamlit as st
import qrcode
from PIL import Image, ImageDraw, ImageFont
import os, json
import pandas as pd

st.set_page_config(layout="wide")
DATA_FILE = "data.json"
LOC_FILE = "locations.json"
ITEMS_DIR = "Items"
os.makedirs(ITEMS_DIR, exist_ok=True)

if os.path.exists(DATA_FILE):
    items = pd.read_json(DATA_FILE, orient="records")
else:
    items = pd.DataFrame(columns=["name", "location", "price", "misc", "barcode_img", "picture_path"])

if os.path.exists(LOC_FILE):
    locations = json.load(open(LOC_FILE))
else:
    locations = []

st.session_state.setdefault("locations", locations)

def save_items():
    items.to_json(DATA_FILE, orient="records")

def save_locations():
    json.dump(st.session_state.locations, open(LOC_FILE, "w"))

def generate_data_qr(item_row):
    content = f"Name: {item_row['name']}\nLocation: {item_row['location']}\nPrice: ${item_row['price']:.2f}\nMisc: {item_row['misc']}"
    qr = qrcode.make(content)
    path = os.path.join(ITEMS_DIR, f"{item_row['name']}_dataqr.png")
    qr.save(path)
    return path

def generate_name_image(name):
    img = Image.new("RGB", (300, 100), color="white")
    d = ImageDraw.Draw(img)
    d.text((10, 30), name, fill="black")
    path = os.path.join(ITEMS_DIR, f"{name}_genpic.png")
    img.save(path)
    return path

def find_item_by_name(name):
    return items[items.name.str.lower() == name.lower()]

st.sidebar.header("📍 Manage Locations")

new_loc = st.sidebar.text_input("Add new location")
if st.sidebar.button("➕ Add"):
    if new_loc and new_loc not in st.session_state.locations:
        st.session_state.locations.append(new_loc)
        save_locations()

loc_to_delete = st.sidebar.selectbox("Delete location", [""] + st.session_state.locations)
if st.sidebar.button("➖ Delete"):
    if loc_to_delete:
        st.session_state.locations.remove(loc_to_delete)
        save_locations()

st.header("📝 Enter or Update Item")

with st.form("item_form"):
    name = st.text_input("Item name")
    loc = st.selectbox("Item location", [""] + st.session_state.locations)
    price = st.number_input("Item price", min_value=0.0, step=0.01)
    misc = st.text_area("Miscellaneous")
    pic = st.file_uploader("Upload picture", type=["png", "jpg", "jpeg"])
    submitted = st.form_submit_button("🔍 Search or Save")

if submitted:
    existing = items[items.name.str.lower() == name.lower()]

    if not name:
        st.error("Please enter an item name.")
    elif not loc:
        st.error("Please select a location.")
    else:
        if not existing.empty:
            idx = existing.index[0]
            items.at[idx, "location"] = loc
            items.at[idx, "price"] = price
            items.at[idx, "misc"] = misc
            st.success(f"Updated existing item: '{name}'")
        else:
            barcode_img = qrcode.make(name)
            barcode_path = os.path.join(ITEMS_DIR, f"{name}_barcode.png")
            barcode_img.save(barcode_path)

            picture_path = ""
            if pic:
                ext = os.path.splitext(pic.name)[1]
                picture_path = os.path.join(ITEMS_DIR, f"{name}_pic{ext}")
                with open(picture_path, "wb") as f:
                    f.write(pic.read())

            items.loc[len(items)] = {
                "name": name,
                "location": loc,
                "price": price,
                "misc": misc,
                "barcode_img": barcode_path,
                "picture_path": picture_path
            }
            st.success(f"Saved new item: '{name}'")

        save_items()

st.header("🧠 Item Tools & Actions")

tool_action = st.selectbox("Choose a function", [
    "", 
    "Generate full-data QR code", 
    "Generate name-based photo", 
    "Find item location from name", 
    "Print QR code", 
    "Print photo", 
    "Print item data", 
    "Save name photo", 
    "Save name QR", 
    "Save name to location"
])

tool_input = st.text_input("Enter item name for selected action")

if tool_input and tool_action:
    result = find_item_by_name(tool_input)
    if result.empty:
        st.warning("Item not found.")
    else:
        row = result.iloc[0]
        if tool_action == "Generate full-data QR code":
            qr_path = generate_data_qr(row)
            st.image(qr_path, caption="Data QR Code", use_container_width=True)

        elif tool_action == "Generate name-based photo":
            img_path = generate_name_image(row['name'])
            st.image(img_path, caption="Name-Based Generated Image", use_container_width=True)

        elif tool_action == "Find item location from name":
            st.info(f"Item location: {row['location']}")

        elif tool_action == "Print QR code":
            st.image(row["barcode_img"], caption="Print: QR Code", use_container_width=True)

        elif tool_action == "Print photo":
            if row["picture_path"] and os.path.exists(row["picture_path"]):
                st.image(row["picture_path"], caption="Print: Photo", use_container_width=True)
            else:
                st.warning("No photo found for this item.")

        elif tool_action == "Print item data":
            st.json({
                "name": row["name"],
                "location": row["location"],
                "price": row["price"],
                "misc": row["misc"]
            })

        elif tool_action == "Save name photo":
            new_path = generate_name_image(row["name"])
            st.success(f"Saved name photo to: {new_path}")

        elif tool_action == "Save name QR":
            qr = qrcode.make(row["name"])
            path = os.path.join(ITEMS_DIR, f"{row['name']}_nameqr.png")
            qr.save(path)
            st.success(f"Saved name QR to: {path}")

        elif tool_action == "Save name to location":
            if row["location"] not in st.session_state.locations:
                st.session_state.locations.append(row["location"])
                save_locations()
                st.success(f"Added '{row['location']}' to location list.")
            else:
                st.info(f"'{row['location']}' already exists in locations.")

st.header("📋 View or Search Items")

search = st.text_input("Search item by name")
if st.button("Search"):
    results = items[items.name.str.contains(search, case=False)] if search else items
    st.dataframe(results[["name", "location", "price", "misc"]], use_container_width=True)

    for i, row in results.iterrows():
        st.subheader(row["name"])
        col1, col2 = st.columns(2)

        with col1:
            st.image(row["barcode_img"], caption="Barcode", use_container_width=True)
            if st.button(f"Print Barcode - {row['name']}"):
                st.write(f"**Print Path:** {row['barcode_img']}")

        with col2:
            if row["picture_path"] and os.path.exists(row["picture_path"]):
                st.image(row["picture_path"], caption="Uploaded Picture", use_container_width=True)

        st.write(f"**Location:** {row['location']}")
        st.write(f"**Price:** ${row['price']:.2f}")
        st.write(f"**Misc:** {row['misc']}")
