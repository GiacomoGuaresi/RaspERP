import os
import base64

def get_category(product_code):
    if product_code.startswith("SA"):
        return "Subassembly"
    elif product_code.startswith("S"):
        return "PrintedPart"
    else:
        return "Component"

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        b64_encoded = base64.b64encode(img_file.read()).decode("utf-8")
        return f"data:image/png;base64,{b64_encoded}"

def generate_sql_inserts(folder_path, output_sql_path="insert_products.sql"):
    insert_lines = []

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".png"):
            product_code = os.path.splitext(filename)[0]
            category = get_category(product_code)
            image_path = os.path.join(folder_path, filename)
            image_base64 = encode_image_to_base64(image_path)

            insert = (
                f"INSERT INTO Product (ProductCode, Category, Metadata, Image) "
                f"VALUES ('{product_code}', '{category}', '{{}}', '{image_base64}');"
            )
            insert_lines.append(insert)

    with open(output_sql_path, "w", encoding="utf-8") as sql_file:
        sql_file.write("\n".join(insert_lines))

    print(f"SQL file created: {output_sql_path}")

# Esempio d'uso
# Cambia il path qui sotto con la cartella contenente le immagini
folder_path = r"C:\\Users\\guare\Desktop\\G1_drawings\\Icons"
generate_sql_inserts(folder_path)
