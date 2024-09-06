import time
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk  # Para usar o Treeview
import json
import os

# Caminho do arquivo onde as despesas serão salvas
CAMINHO_ARQUIVO = "despesas.json"

# Função para carregar despesas do arquivo JSON
def carregar_despesas():
    if os.path.exists(CAMINHO_ARQUIVO):
        with open(CAMINHO_ARQUIVO, "r") as f:
            despesas_carregadas = json.load(f)
            for despesa in despesas_carregadas:
                despesa['vencimento'] = datetime.strptime(despesa['vencimento'], "%Y-%m-%d")
                if despesa.get('data_pagamento'):
                    despesa['data_pagamento'] = datetime.strptime(despesa['data_pagamento'], "%Y-%m-%d")
            return despesas_carregadas
    return []

# Função para salvar as despesas no arquivo JSON
def salvar_despesas():
    with open(CAMINHO_ARQUIVO, "w") as f:
        despesas_para_salvar = [
            {
                'nome': d['nome'], 
                'valor': d['valor'], 
                'vencimento': d['vencimento'].strftime("%Y-%m-%d"), 
                'tipo': d['tipo'], 
                'paga': d['paga'],
                'data_pagamento': d['data_pagamento'].strftime("%Y-%m-%d") if d.get('data_pagamento') else None
            } 
            for d in despesas
        ]
        json.dump(despesas_para_salvar, f, indent=4)

# Função para adicionar despesas
def adicionar_despesa():
    nome = entry_nome.get()
    valor_str = entry_valor.get().replace(",", ".")
    
    try:
        valor = float(valor_str)
    except ValueError:
        messagebox.showerror("Erro", "Por favor, insira um valor válido.")
        return
    
    try:
        data_vencimento = datetime.strptime(entry_data.get(), "%d/%m/%Y")
    except ValueError:
        messagebox.showerror("Erro", "Por favor, insira a data no formato dd/mm/yyyy.")
        return
    
    tipo_despesa = tipo_var.get()  # Verifica se é única ou recorrente
    
    despesas.append({"nome": nome, "valor": valor, "vencimento": data_vencimento, "tipo": tipo_despesa, "paga": False, "data_pagamento": None})
    salvar_despesas()
    messagebox.showinfo("Sucesso", f"Despesa '{nome}' adicionada com sucesso!")
    limpar_campos()
    atualizar_tabelas()

# Função para atualizar as tabelas de contas pagas e não pagas
def atualizar_tabelas():
    for row in tree_nao_pagas.get_children():
        tree_nao_pagas.delete(row)  # Limpar a tabela de contas não pagas
    for row in tree_pagas.get_children():
        tree_pagas.delete(row)  # Limpar a tabela de contas pagas

    total_nao_pagas = 0
    total_pagas = 0

    # Separar as despesas em pagas e não pagas
    despesas_nao_pagas = [d for d in despesas if not d['paga']]
    despesas_pagas = [d for d in despesas if d['paga']]

    # Preencher a tabela de contas não pagas
    despesas_ordenadas_nao_pagas = sorted(despesas_nao_pagas, key=lambda x: x['vencimento'])
    for despesa in despesas_ordenadas_nao_pagas:
        tree_nao_pagas.insert('', 'end', values=(despesa['nome'], f"R${despesa['valor']:.2f}", despesa['vencimento'].strftime("%d/%m/%Y"), despesa['tipo']))
        total_nao_pagas += despesa['valor']

    # Preencher a tabela de contas pagas
    despesas_ordenadas_pagas = sorted(despesas_pagas, key=lambda x: x['vencimento'])
    for despesa in despesas_ordenadas_pagas:
        tree_pagas.insert('', 'end', values=(despesa['nome'], f"R${despesa['valor']:.2f}", despesa['vencimento'].strftime("%d/%m/%Y"), despesa['tipo']))
        total_pagas += despesa['valor']

    # Atualizar o total embaixo de cada tabela
    label_total_nao_pagas.config(text=f"Total: R${total_nao_pagas:.2f}")
    label_total_pagas.config(text=f"Total: R${total_pagas:.2f}")

# Função para verificar despesas recorrentes e reativá-las após 25 dias
def verificar_despesas_recorrentes():
    for despesa in despesas:
        if despesa['tipo'] == 'Recorrente' and despesa['paga'] and despesa.get('data_pagamento'):
            # Verificar se já se passaram 25 dias desde a data de pagamento
            if (datetime.now() - despesa['data_pagamento']).days >= 25:
                # Reativar a despesa, marcando-a como não paga e atualizando a data de vencimento
                despesa['paga'] = False
                despesa['vencimento'] += timedelta(days=25)  # Atualizar a data de vencimento
                despesa['data_pagamento'] = None  # Remover a data de pagamento
    salvar_despesas()

# Função para marcar uma despesa como paga
def pagar_despesa():
    try:
        # Obter o item selecionado na tabela de contas não pagas
        selected_item = tree_nao_pagas.selection()[0]
        valores = tree_nao_pagas.item(selected_item, 'values')

        # Encontrar a despesa pelo nome, valor e data de vencimento
        despesa_a_pagar = next((d for d in despesas if d['nome'] == valores[0] and d['valor'] == float(valores[1][2:].replace(",", ".")) and d['vencimento'].strftime("%d/%m/%Y") == valores[2]), None)

        if despesa_a_pagar:
            despesa_a_pagar['paga'] = True
            despesa_a_pagar['data_pagamento'] = datetime.now()  # Armazenar a data de pagamento
            salvar_despesas()
            messagebox.showinfo("Sucesso", f"Despesa '{despesa_a_pagar['nome']}' marcada como paga.")
            atualizar_tabelas()
    except IndexError:
        messagebox.showerror("Erro", "Selecione uma despesa para pagar.")

# Função para remover despesa (de qualquer tabela)
def remover_despesa():
    try:
        # Verificar se o item selecionado está na tabela de contas não pagas
        selected_item = tree_nao_pagas.selection() or tree_pagas.selection()
        if selected_item:
            valores = tree_nao_pagas.item(selected_item[0], 'values') if tree_nao_pagas.selection() else tree_pagas.item(selected_item[0], 'values')

            # Encontrar a despesa pelo nome, valor e data de vencimento
            despesa_a_remover = next((d for d in despesas if d['nome'] == valores[0] and d['valor'] == float(valores[1][2:].replace(",", ".")) and d['vencimento'].strftime("%d/%m/%Y") == valores[2]), None)

            if despesa_a_remover:
                despesas.remove(despesa_a_remover)
                salvar_despesas()
                messagebox.showinfo("Sucesso", f"Despesa '{despesa_a_remover['nome']}' removida com sucesso.")
                atualizar_tabelas()
    except IndexError:
        messagebox.showerror("Erro", "Selecione uma despesa para remover.")

# Função para mostrar as despesas que vencem hoje
def mostrar_vencendo_hoje():
    data_atual = datetime.now().date()
    
    for row in tree_nao_pagas.get_children():
        tree_nao_pagas.delete(row)  # Limpar a tabela de contas não pagas
    
    despesas_vencendo_hoje = [d for d in despesas if not d['paga'] and d['vencimento'].date() == data_atual]
    
    for despesa in despesas_vencendo_hoje:
        tree_nao_pagas.insert('', 'end', values=(despesa['nome'], f"R${despesa['valor']:.2f}", despesa['vencimento'].strftime("%d/%m/%Y"), despesa['tipo']))

    if not despesas_vencendo_hoje:
        messagebox.showinfo("Info", "Não há despesas vencendo hoje.")

# Função para mostrar todas as despesas
def mostrar_todas_despesas():
    atualizar_tabelas()  # Chama a função que já atualiza todas as despesas

# Função para limpar campos
def limpar_campos():
    entry_nome.delete(0, tk.END)
    entry_valor.delete(0, tk.END)
    entry_data.delete(0, tk.END)
    tipo_var.set("Única")

# Lista para armazenar as despesas (carrega as despesas salvas ao iniciar)
despesas = carregar_despesas()

# Verificar despesas recorrentes ao iniciar
verificar_despesas_recorrentes()

# Criação da interface gráfica
root = tk.Tk()
root.title("Gerenciador de Despesas")
root.geometry("900x950")  # Janela com tamanho 800x800
root.configure(bg="#155fdb")  # Alterar para um azul mais profundo

# Carregar a logo
logo = tk.PhotoImage(file=r"C:\Users\Usuário\Downloads\escLogo.png")
logo_label = tk.Label(root, image=logo, bg="#155fdb")
logo_label.grid(row=0, column=0, columnspan=2, pady=10)

# Labels e Entry para nome, valor e data de vencimento
tk.Label(root, text="Nome da Despesa:", bg="#155fdb", fg="white").grid(row=1, column=0, padx=10, pady=5)
entry_nome = tk.Entry(root)
entry_nome.grid(row=1, column=1, padx=10, pady=5)

tk.Label(root, text="Valor da Despesa (R$):", bg="#155fdb", fg="white").grid(row=2, column=0, padx=10, pady=5)
entry_valor = tk.Entry(root)
entry_valor.grid(row=2, column=1, padx=10, pady=5)

tk.Label(root, text="Data de Vencimento (dd/mm/yyyy):", bg="#155fdb", fg="white").grid(row=3, column=0, padx=10, pady=5)
entry_data = tk.Entry(root)
entry_data.grid(row=3, column=1, padx=10, pady=5)

# RadioButtons para selecionar o tipo da despesa (Única ou Recorrente)
tipo_var = tk.StringVar(value="Única")
tk.Label(root, text="Tipo da Despesa:", bg="#155fdb", fg="white").grid(row=4, column=0, padx=10, pady=5)
radio_unica = tk.Radiobutton(root, text="Única", variable=tipo_var, value="Única", bg="#155fdb", fg="white")
radio_unica.grid(row=4, column=1, sticky="w")
radio_recorrente = tk.Radiobutton(root, text="Recorrente", variable=tipo_var, value="Recorrente", bg="#155fdb", fg="white")
radio_recorrente.grid(row=4, column=1, sticky="e")

# Botão para adicionar despesa
btn_add = tk.Button(root, text="Adicionar Despesa", command=adicionar_despesa)
btn_add.grid(row=5, column=0, columnspan=2, padx=10, pady=10)

# Frame para a tabela de contas não pagas e barra de rolagem
frame_tabela_nao_pagas = tk.Frame(root)
frame_tabela_nao_pagas.grid(row=6, column=0, columnspan=2, padx=10, pady=10)

scrollbar_nao_pagas = tk.Scrollbar(frame_tabela_nao_pagas)
scrollbar_nao_pagas.pack(side=tk.RIGHT, fill=tk.Y)

tree_nao_pagas = ttk.Treeview(frame_tabela_nao_pagas, columns=("nome", "valor", "vencimento", "tipo"), show='headings', yscrollcommand=scrollbar_nao_pagas.set)
tree_nao_pagas.heading("nome", text="Nome da Despesa")
tree_nao_pagas.heading("valor", text="Valor")
tree_nao_pagas.heading("vencimento", text="Data de Vencimento")
tree_nao_pagas.heading("tipo", text="Tipo")
tree_nao_pagas.pack(side=tk.LEFT)

scrollbar_nao_pagas.config(command=tree_nao_pagas.yview)

# Label para mostrar o total das contas não pagas
label_total_nao_pagas = tk.Label(root, text="Total: R$0.00", bg="#155fdb", fg="white", font=("Arial", 12))
label_total_nao_pagas.grid(row=7, column=0, columnspan=2, pady=10)

# Frame para a tabela de contas pagas e barra de rolagem
frame_tabela_pagas = tk.Frame(root)
frame_tabela_pagas.grid(row=8, column=0, columnspan=2, padx=10, pady=10)

scrollbar_pagas = tk.Scrollbar(frame_tabela_pagas)
scrollbar_pagas.pack(side=tk.RIGHT, fill=tk.Y)

tree_pagas = ttk.Treeview(frame_tabela_pagas, columns=("nome", "valor", "vencimento", "tipo"), show='headings', yscrollcommand=scrollbar_pagas.set)
tree_pagas.heading("nome", text="Nome da Despesa")
tree_pagas.heading("valor", text="Valor")
tree_pagas.heading("vencimento", text="Data de Vencimento")
tree_pagas.heading("tipo", text="Tipo")
tree_pagas.pack(side=tk.LEFT)

scrollbar_pagas.config(command=tree_pagas.yview)

# Label para mostrar o total das contas pagas
label_total_pagas = tk.Label(root, text="Total: R$0.00", bg="#155fdb", fg="white", font=("Arial", 12))
label_total_pagas.grid(row=9, column=0, columnspan=2, pady=10)

# Frame para conter os botões centralizados
frame_botoes = tk.Frame(root, bg="#155fdb")  # Cor de fundo opcional para combinar com o restante do layout
frame_botoes.grid(row=10, column=0, columnspan=2, pady=10, padx=10, sticky="ew")  # Centralizar na tela com columnspan e sticky

# Botão para pagar despesa selecionada
btn_pagar = tk.Button(frame_botoes, text="Pagar Despesa", command=pagar_despesa)
btn_pagar.grid(row=0, column=0, padx=5, pady=10)

# Botão para remover despesa selecionada
btn_remover = tk.Button(frame_botoes, text="Remover Despesa", command=remover_despesa)
btn_remover.grid(row=0, column=1, padx=5, pady=10)

# Botão para mostrar despesas vencendo hoje
btn_vencendo_hoje = tk.Button(frame_botoes, text="Vencendo Hoje", command=mostrar_vencendo_hoje)
btn_vencendo_hoje.grid(row=0, column=2, padx=5, pady=10)

# Botão para mostrar todas as despesas
btn_mostrar_todas = tk.Button(frame_botoes, text="Mostrar Todas as Despesas", command=mostrar_todas_despesas)
btn_mostrar_todas.grid(row=0, column=3, padx=5, pady=10)


# Preencher as tabelas com as despesas salvas
atualizar_tabelas()

# Rodar o loop principal da interface gráfica
root.mainloop()
