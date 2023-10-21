import fitz
import re
import csv
from pypdf import PdfReader, PdfWriter

from flask import Flask, jsonify, request



paginasErradas = set()

linhasParaArquivoCsv = []


def timeStringToMinutes(horaString):
    if horaString == '' or horaString == ' ':
        return False
    horas, minutos = horaString.split(':')
    valorHoras = int(horas) * 60
    valorMinutosTotais = valorHoras + int(minutos)

    return valorMinutosTotais

def executaFuncoes(tuplaValoresDia, numeroPagina, listaPaginasNaoLer):
    
    listaParaNaoLer = ['EMPRESA', 'ENDEREÇO', 'FUNC.', 'DIA']
    listaSiglasNaoTrabalhadas = ['FN', 'DC', 'FX', 'DF', 'AM', 'DA', 'AF', 'FR', 'SE', 'FJ', 'SU', 'FA', 'AE', 'AD', 'LS', 'LC', 'MT', 'AP']
    linhasPlacaExcessiva = ['EPT03', 'EPT22']
    

    if tuplaValoresDia[0] in listaParaNaoLer or str(numeroPagina) in listaPaginasNaoLer:
        return None

    def trataDiaLancamento(tuplaValoresDia):
        diaNumero, diaSemana = tuplaValoresDia[0].split(' ')
        if 3 > len(tuplaValoresDia[1].split(' ')) > 1:
            lancamento, guia = tuplaValoresDia[1].split(' ')
        elif len(tuplaValoresDia[1].split(' ')) > 2:
            listaIndex1 = tuplaValoresDia[1].split(' ')
            lancamento, guia = listaIndex1[0:2]
            inicioViagem = listaIndex1[2]
            return [diaNumero, diaSemana, lancamento, guia, inicioViagem] + tuplaValoresDia[2:]
        else:
            lancamento = tuplaValoresDia[1]
            guia = None
        return [diaNumero, diaSemana, lancamento, guia] + tuplaValoresDia[2:]
    
    novaLista = trataDiaLancamento(tuplaValoresDia)

    

    if novaLista[2] in listaSiglasNaoTrabalhadas:
        return None
    
    if len(novaLista) < 14:
        paginasErradas.add(numeroPagina)
        linhasParaArquivoCsv.append((numeroPagina + 1, novaLista, 'ListaMenor'))
        return None
    



    
    def verificaFimDeViagem(tuplaValoresDia, numeroPagina):    

        fimViagem = timeStringToMinutes(tuplaValoresDia[6])
        fimJornada = timeStringToMinutes(tuplaValoresDia[7])
        inicioJornada = timeStringToMinutes(tuplaValoresDia[4])
        inicioViagem = timeStringToMinutes(tuplaValoresDia[5])
        linha = tuplaValoresDia[3]


        if fimViagem == False or fimJornada == False:
            return False
        
        if fimJornada < 240:
            fimJornada = 1440 + fimJornada
        if fimViagem < 240:
            fimViagem = 1440 + fimViagem

        if fimViagem > fimJornada and fimViagem - fimJornada > 30:
            paginasErradas.add(numeroPagina)
            linhasParaArquivoCsv.append((numeroPagina+1, novaLista, 'Fim de Viagem'))
            return None
        
        if fimViagem > fimJornada and linha != None and linha[0] == 'E':
            paginasErradas.add(numeroPagina)
            linhasParaArquivoCsv.append((numeroPagina+1, novaLista, 'Fim de Viagem EPT'))
            return None
        
        if inicioViagem < inicioJornada:
            paginasErradas.add(numeroPagina)
            linhasParaArquivoCsv.append((numeroPagina+1, novaLista, 'Inicio Viagem antes de FimJornada'))
            return None

        elif fimJornada - fimViagem > 180:
            paginasErradas.add(numeroPagina)
            linhasParaArquivoCsv.append((numeroPagina +1, novaLista, 'Largada Demorada'))
            return None
        
    def verificaHorasNegativas(tuplaValoresDia, numeroPagina):
        cargaHoraria = str(tuplaValoresDia[9])

        if cargaHoraria != '' and cargaHoraria[0] == '-':
            paginasErradas.add(numeroPagina)
            linhasParaArquivoCsv.append((numeroPagina+1, novaLista, 'HoraNegativa'))
            return None
    
    def verificaLinhaVazia(tuplaValoresDia, numeroPagina):
        linha = tuplaValoresDia[3]
        sigla = tuplaValoresDia[2]

        if linha == '' or linha == None and sigla == 'DT':
            paginasErradas.add(numeroPagina)
            linhasParaArquivoCsv.append((numeroPagina+1, novaLista, 'linhaVazia'))
            return None

    def verificaPlacaSuperior(tuplaValoresDia, numeroPagina):
        tempoDePlaca = timeStringToMinutes(tuplaValoresDia[8])
        linha = tuplaValoresDia[3]
        
        if tempoDePlaca > 180 and linha not in linhasPlacaExcessiva:
            paginasErradas.add(numeroPagina)
            linhasParaArquivoCsv.append((numeroPagina+1, novaLista, 'PlacaExcessiva'))
            return None
        

    return verificaFimDeViagem(novaLista, numeroPagina), verificaHorasNegativas(novaLista, numeroPagina), verificaLinhaVazia(novaLista, numeroPagina), verificaPlacaSuperior(novaLista, numeroPagina)
    

def percorrePaginas(pdfPathOrigem, listaPaginasString):
    pdf_document = fitz.open(pdfPathOrigem)

    for numeroPagina in range(pdf_document.page_count):
        paginaElement = pdf_document[numeroPagina]

    

        targetX = 31.18000030517578
        
        for block in paginaElement.get_text('blocks', sort=True):
            x, y, widht, height = block[0:4]
            texto = block[4]
            if x == targetX:
                
                valorSeparado = list(re.split(r'\n', texto))
                executaFuncoes(valorSeparado, numeroPagina, listaPaginasString)

def escreveArquivoLista(lista, path):
    try:
        with open(path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter=';')

            for tup in lista:
                writer.writerow(tup)
    except PermissionError:
        print('Erro ao escrever o arquivo. Ele provavelmente está aberto.')
    
def escreveArquivoErrados(lista, path, outputPath):

    pdf_writer = PdfWriter()
    pdf_reader = PdfReader(path)

    for pagina in range(0 ,len(pdf_reader.pages)):
        if pagina in lista:
            pdf_writer.add_page(page= pdf_reader.pages[int(pagina)])
    
    with open(f'{outputPath} errados.pdf', 'wb') as fh:
        pdf_writer.write(fh)

def escreveArquivoCertos(lista, path, outputPath):

    pdf_writer = PdfWriter()
    pdf_reader = PdfReader(path)

    for pagina in range(0, len(pdf_reader.pages)):
        if pagina not in lista:
            pdf_writer.add_page(page= pdf_reader.pages[int(pagina)])
    
    with open(f'{outputPath}certos.pdf', 'wb') as fh:
        pdf_writer.write(fh)

def trataPathEscrita(path):
    if path.endswith('.csv') or path.endswith('.pdf'):
        path = path[0:-3]
    return path


app = Flask (__name__)

@app.route('/api', defaults={'path': '/api'}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def options(path):
    response = jsonify({'message': 'CORS preflight request successful'})
    response.headers['Access-Control-Allow-Origin'] = '*'  # Update with your allowed origin(s)
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/api', methods=['POST'])
def enviaDados():
    

    listaPaginasString = str(request.json['paginasNaoLer'])
    pathLeitura = request.json['pathInput']
    if pathLeitura.startswith('"') and pathLeitura.endswith('"'):
        pathLeitura = pathLeitura[1:-1]
    
    pathEscrita = request.json['pathOutput']
    if pathEscrita.startswith('"') and pathEscrita.endswith('"'):
        pathEscrita = pathEscrita[1:-1]

    percorrePaginas(rf"{pathLeitura}", listaPaginasString)
    print(paginasErradas, len(paginasErradas))
    escreveArquivoLista(linhasParaArquivoCsv, rf"{pathEscrita}")
    escreveArquivoCertos(paginasErradas, pathLeitura, trataPathEscrita(pathEscrita))
    escreveArquivoErrados(paginasErradas, pathLeitura, trataPathEscrita(pathEscrita))

    return jsonify({'resposta': 'funcionou'}), 201



if __name__ == '__main__':
    ...
    app.run(port = 8080)

""" listaPaginasString = str(input('Digite as paginas que não deseja ler: '))
pathLeitura = str(input('Digite o caminho do arquivo que você quer ler: '))
if pathLeitura.startswith('"') and pathLeitura.endswith('"'):
    pathLeitura = pathLeitura[1:-1]
percorrePaginas(rf"{pathLeitura}", listaPaginasString)
print(paginasErradas, len(paginasErradas))
pathEscrita = str(input('Digite o caminho do arquivo que você quer escrever: '))
if pathEscrita.startswith('"') and pathEscrita.endswith('"'):
    pathEscrita = pathEscrita[1:-1]

escreveArquivoLista(linhasParaArquivoCsv, rf"{pathEscrita}")
escreveArquivoCertos(paginasErradas, pathLeitura, trataPathEscrita(pathEscrita))
escreveArquivoErrados(paginasErradas, pathLeitura, trataPathEscrita(pathEscrita)) """
