new_students = {
    'Сириус Блэк': 'отвага',
    'Аманда Коршун': 'знание',
    'Пенелопа Вулпинголд': 'находчивость',
    'Артур Поттер': 'отвага',
    'Тесая Блэк': 'изобретательность'
}
def sorting_hat(students):
    quality_to_house = {
        'отвага': 'Гриффиндор', 'доброта': 'Гриффиндор', 'решительность': 'Гриффиндор',
        'усердие': 'Пуффендуй', 'дружелюбие': 'Пуффендуй', 'терпимость': 'Пуффендуй',
        'знание': 'Когтевран', 'изобретательность': 'Когтевран', 'рассудительность': 'Когтевран',
        'амбиции': 'Слизерин', 'находчивость': 'Слизерин', 'целеустремленность': 'Слизерин'
    }


    assigned = {}
    for name, quality in students.items():
        house = quality_to_house[quality]
        assigned[name] = house

    sorted_students = {}
    for name in sorted(assigned, key=lambda x: (assigned[x], x)):
        sorted_students[name] = assigned[name]

    departments = {house: 0 for house in ['Гриффиндор', 'Пуффендуй', 'Когтевран', 'Слизерин']}
    for house in assigned.values():
        departments[house] += 1

    departments = {house: departments[house] for house in sorted(departments)}

    return sorted_students, departments

print(sorting_hat(new_students))