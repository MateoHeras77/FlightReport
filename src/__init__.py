# Mover archivos debug_supabase.py e insert_test_data.py a la carpeta scripts
import os
import shutil

# Crear la carpeta scripts si no existe
scripts_dir = os.path.join(os.path.dirname(__file__), 'scripts')
os.makedirs(scripts_dir, exist_ok=True)

# Mover archivos
files_to_move = ['debug_supabase.py', 'insert_test_data.py']
for file_name in files_to_move:
    src_path = os.path.join(os.path.dirname(__file__), file_name)
    dest_path = os.path.join(scripts_dir, file_name)
    if os.path.exists(src_path):
        shutil.move(src_path, dest_path)
        print(f'Movido {file_name} a {scripts_dir}')
    else:
        print(f'Archivo {file_name} no encontrado en {os.path.dirname(__file__)}')