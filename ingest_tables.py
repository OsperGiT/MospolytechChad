from db import create_collection, add_documents
from docx import Document

# Импортировать данные из докс таблицы с проходнными баллами (предварительно надо отредактировать и положить информацию о форме обучения во второй столбец заголовка: очное, заочное, очно-заочное)
def extract_lines_from_doxc(doc):
    list = []
    education_form = "not difined"
    for table in doc.tables:
        for row in table.rows:
            values = [cell.text.replace("\n", " ") for cell in row.cells]
            if "очно-заочное" in values[1]:
                education_form = "очно-заочная"
                continue
            elif "заочное" in values[1]:
                education_form = "заочная"
                continue
            elif "очное" in values[1]:
                education_form = "очная"
                continue
            elif "ВСЕГО" in values[1]:
                continue
            else:
                name = values[1]
                passing_budget = values[5]
                passing_paid = values[9]

                chunk_text = f"Название направления: {name} | Форма обучения: {education_form} | Проходной балл на бюджет: {passing_budget} | Средний балл на платную основу: {passing_paid}"
                list.append(chunk_text)
    return list

# функция для перевода списка списков (вложенный список содержит данные по каждому направлению) в список строк (вложенный список преобразуем с строку)
def list_to_string(rows):
    chunks_text = []

    for row in rows:  # rows — твой список списков
        # Объединяем все элементы одной строки через понятный разделитель
        text = " | ".join(row)
        chunks_text.append(text)
    return chunks_text

# Путь к документу
doc = Document("E://RAG_Documents//bakalavr_2025.docx")

points_list = extract_lines_from_doxc(doc)
# chunks_text = list_to_string(points_list)

# проверка чанков
# x = 1
# while x != 0:
#     print(points_list[int(x)], "\n")
#     x = input("Номер чанка: ")
collection_name = create_collection("docs")
add_documents(collection_name, points_list, topics = "бакалавриат")
