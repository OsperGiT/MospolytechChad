from db import create_collection, add_documents_structured
from docx import Document

# Импортировать данные из докс таблицы с проходнными баллами (предварительно надо отредактировать и положить информацию о форме обучения во второй столбец заголовка: очное, заочное, очно-заочное)

def extract_lines_from_doxc(doc):
    """
    Преобразует таблицу Word в список плоских чанков для ChromaDB.
    Каждый профиль создаёт отдельный документ с плоскими метаданными.
    """
    chunks = []
    major_id = None
    secondary_id = None
    current_major = None
    current_major_id = None

    for table in doc.tables:
        for row in table.rows:
            values = [cell.text.replace("\n", " ").strip() for cell in row.cells]

            # Определяем major_id и secondary_id
            if len(values[0]) == 8:  # обобщающее название
                major_id = values[0]
                current_major_id = major_id
                secondary_id = None
            elif len(values[0]) > 8:  # профиль
                secondary_id = values[0]

            # Определяем название направления
            if major_id and secondary_id and major_id[:8] == secondary_id[:8]:
                major_name = current_major  # оставляем текущее направление
            else:
                major_name = values[1]
                current_major = major_name  # сохраняем на будущее

            # Определяем форму обучения
            if "очно-заочное" in values[1].lower():
                education_form = "очно-заочная"
                continue
            elif "заочное" in values[1].lower():
                education_form = "заочная"
                continue
            elif "очное" in values[1].lower():
                education_form = "очная"
                continue
            elif "ВСЕГО" in values[1]:
                continue

            # Сохраняем профиль и баллы
            if values[5]:
                profile_name = values[1]
                passing_budget = values[5]
                passing_paid = values[9]

                # Создаём отдельный документ для каждого профиля
                chunk = {
                    "direction": major_name,
                    "form": education_form,
                    "major_id": current_major_id,
                    "profile": profile_name,
                    "passing_budget": passing_budget,
                    "passing_paid": passing_paid,
                    "secondary_id": secondary_id
                }
                chunks.append(chunk)

    return chunks

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
# while x != 'exit':
#     print(points_list[int(x)], "\n")
#     x = input("Номер чанка: ")

collection_name = create_collection("docs")
add_documents_structured(collection_name, points_list, topics = "проходной балл")