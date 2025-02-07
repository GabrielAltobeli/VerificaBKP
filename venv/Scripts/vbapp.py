import os
import pandas as pd
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkinter import filedialog
from tkcalendar import DateEntry
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import errno
from PIL import Image, ImageTk

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Função para autenticar com o Google Drive
def authenticate_gdrive():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('drive', 'v3', credentials=creds)
    return service


# Função para carregar a lista de clientes de um arquivo
def load_clients(client_file='clientes.txt'):
    if os.path.exists(client_file):
        with open(client_file, 'r') as file:
            clients = file.read().splitlines()
        return clients
    else:
        return []


# Função para salvar um novo cliente no arquivo local
def save_client(client_name, client_file='clientes.txt'):
    if client_name and client_name not in load_clients(client_file):
        with open(client_file, 'a') as file:
            file.write(client_name + '\n')
        return True
    return False


# Função para buscar o ID da pasta do cliente
def get_client_folder_id(service, client_name):
    query = f"name contains '{client_name}' and mimeType = 'application/vnd.google-apps.folder'"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    folders = results.get('files', [])
    if not folders:
        return None
    return folders[0]['id']


# Função para buscar arquivos .zip dentro da pasta e subpastas e filtrar pela data
def search_files_in_folder(service, folder_id, client_name, target_date):
    query = f"'{folder_id}' in parents"
    results = service.files().list(q=query, pageSize=1000, fields="files(id, name, modifiedTime, mimeType)").execute()
    files = results.get('files', [])

    file_list = []

    for file in files:
        if file['mimeType'] == 'application/vnd.google-apps.folder':
            # Se for uma subpasta, entra nela recursivamente
            file_list += search_files_in_folder(service, file['id'], client_name, target_date)
        elif 'name' in file and 'modifiedTime' in file and file['mimeType'] == 'application/zip':
            # Verifica se o arquivo termina com .zip
            if file['name'].endswith('.zip'):
                file_mod_time = pd.to_datetime(file['modifiedTime']).strftime('%d/%m/%Y')
                if file_mod_time == target_date:
                    file_list.append({
                        'Cliente': client_name,
                        'Arquivo': file['name'],
                        'Data de Modificação': file_mod_time
                    })

    return file_list


# Função principal para execução do script
def run_script(client_names, target_date):
    try:
        service = authenticate_gdrive()
        not_found_clients = []
        all_data = []

        for client_name in client_names:
            folder_id = get_client_folder_id(service, client_name)
            if folder_id:
                data = search_files_in_folder(service, folder_id, client_name, target_date)
                if data:
                    all_data.extend(data)
                else:
                    not_found_clients.append(client_name)
            else:
                not_found_clients.append(client_name)

        if all_data:
            try:
                df = pd.DataFrame(all_data)
                df.to_excel('relatorio_clientes.zip.xlsx', index=False)
                messagebox.showinfo("Sucesso", "Planilha criada com sucesso!")
            except PermissionError as e:
                if e.errno == errno.EACCES:
                    messagebox.showerror("Erro de Permissão",
                                         "Erro de permissão: A planilha está aberta ou não pode ser acessada.")
                else:
                    messagebox.showerror("Erro", f"Erro ao salvar a planilha: {e}")
            except Exception as e:
                messagebox.showerror("Erro", f"Ocorreu um erro ao salvar a planilha: {e}")
        else:
            messagebox.showinfo("Info", f"Nenhum arquivo .zip encontrado em {target_date}.")

        return not_found_clients

    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro ao executar o script: {e}")
        return []


# Função para adicionar novo cliente à lista
def add_client():
    client_name = entry_client.get().strip()
    if client_name:
        if save_client(client_name):
            listbox_clients.insert(tk.END, client_name)
            entry_client.delete(0, tk.END)
            messagebox.showinfo("Sucesso", "Cliente adicionado com sucesso!")
        else:
            messagebox.showerror("Erro", "Cliente já existe ou nome inválido.")
    else:
        messagebox.showerror("Erro", "Nome do cliente não pode estar vazio.")


# Função para executar o script
def execute_script():
    target_date = date_picker.get_date().strftime('%d/%m/%Y')
    client_names = load_clients()
    not_found_clients = run_script(client_names, target_date)

    # Atualizar o DataGridView com os clientes que não tiveram arquivos encontrados
    update_not_found_grid(not_found_clients)


# Função para atualizar o DataGridView
def update_not_found_grid(not_found_clients):
    for row in treeview.get_children():
        treeview.delete(row)
    for client in not_found_clients:
        treeview.insert('', 'end', values=(client,))

# Obter o caminho da pasta onde o script está sendo executado
current_dir = os.path.dirname(os.path.abspath(__file__))

# Caminho relativo para o ícone
icon_path = os.path.join(current_dir, 'ZIP.ico')

# Inicializar janela principal
root = tk.Tk()
root.title("Verifica Backup")

# Definir o ícone da janela (personalizado .ico)
icon_image = ImageTk.PhotoImage(Image.open(icon_path))
root.iconphoto(True, icon_image)

# Campo para adicionar novo cliente
label_client = tk.Label(root, text="Adicionar Cliente:")
label_client.grid(row=0, column=0, padx=5, pady=5)
entry_client = tk.Entry(root)
entry_client.grid(row=0, column=1, padx=5, pady=5)
btn_add_client = tk.Button(root, text="Salvar Cliente", command=add_client)
btn_add_client.grid(row=0, column=2, padx=5, pady=5)

# Lista de clientes (Listbox)
label_client_list = tk.Label(root, text="Clientes Atuais:")
label_client_list.grid(row=1, column=0, padx=5, pady=5)
listbox_clients = tk.Listbox(root, height=6, width=40)
listbox_clients.grid(row=1, column=1, columnspan=2, padx=5, pady=5)
for client in load_clients():
    listbox_clients.insert(tk.END, client)

# Data Picker para selecionar a data
label_date = tk.Label(root, text="Selecionar Data:")
label_date.grid(row=2, column=0, padx=5, pady=5)
date_picker = DateEntry(root, date_pattern='dd/mm/yyyy')
date_picker.grid(row=2, column=1, padx=5, pady=5)

# Botão para executar o script
btn_execute = tk.Button(root, text="Executar Script", command=execute_script)
btn_execute.grid(row=3, column=1, padx=5, pady=10)

# Grid para exibir clientes que não foram encontrados
label_not_found = tk.Label(root, text="Clientes não encontrados:")
label_not_found.grid(row=4, column=0, padx=5, pady=5)
treeview = ttk.Treeview(root, columns=("Cliente"), show='headings')
treeview.heading("Cliente", text="Cliente")
treeview.grid(row=5, column=0, columnspan=3, padx=5, pady=5)

# Inicializar a janela
root.mainloop()
