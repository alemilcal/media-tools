import requests
import os
import sys

# Configuración
API_KEY = "Q5i9yCmsFJ41wbXX0zwEECE6y8IrCm18NQeRTgDP7240b503"
BASE_URL = "https://api.theporndb.net/scenes/parse"

def descargar_poster(nombre_archivo_completo):
    # 1. Extraer nombre sin extensión
    nombre_sin_ext, _ = os.path.splitext(nombre_archivo_completo)

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json"
    }
    
    try:
        # 2. Búsqueda en API
        response = requests.get(BASE_URL, headers=headers, params={"name": nombre_sin_ext})
        response.raise_for_status()
        data = response.json()

        image_url = data.get('data', {}).get('image')
        if not image_url:
            print(f"[-] No se encontró imagen para: {nombre_sin_ext}")
            return

        # 3. Descarga de imagen
        img_res = requests.get(image_url)
        img_res.raise_for_status()

        # Determinar extensión de la imagen
        _, img_ext = os.path.splitext(image_url)
        img_ext = img_ext if img_ext else ".jpg"

        # 4. Guardar archivo
        nombre_salida = f"{nombre_sin_ext}{img_ext}"
        with open(nombre_salida, 'wb') as f:
            f.write(img_res.content)
        
        print(f"[+] Guardado: {nombre_salida}")

    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    # Verificar si se pasó el argumento
    if len(sys.argv) < 2:
        print("Uso: python script.py <nombre_del_archivo>")
        sys.exit(1)

    archivo_input = sys.argv[1]
    descargar_poster(archivo_input)