import re
import requests

from datetime import datetime

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, FSInputFile

from constants.paths_constants import QR_CODE_PATH, CREDIT_VERIFICATION_INSTRUCTIONS_PATH
from keyboards.user import (
    kb_yn, kb_2, kb_3, kb_4,
    kb_back, kb_check_data,
    kb_approval, kb_phone_number, kb_get_phone_number)
from states.user import Form
from services.service import Service
from handlers.manager import start_mailing_to_managers
from settings.config import TOKEN_METRICA


async def get_requests(tid, cid, ea):
    ms = TOKEN_METRICA
    dr = "https://t.me/Odobri_credit_bot"

    response = requests.get(f"https://mc.yandex.ru/collect/?tid={tid}&cid={cid}&t=event&dr={dr}&ea={ea}&ms={ms}")


def mes_form_maker(data):
    mes = f'Пожалуйста, проверьте все ли верно:\n' + \
            f'- Ваше имя: {data.get("name")}\n' + \
            f'- Регион, где планируете взять кредит: {data.get("region")}\n' + \
            f'- Есть ли у вас судимость: {data.get("criminal_record")}\n'
    if data.get("criminal_record") == "✅Да":
        mes += f'- Судимость действующая: {data.get("is_criminal_record")}\n'
        if data.get("is_criminal_record") == "❌Нет":
            mes += f'- Судимость погашена в {data.get("end_of_the_criminal_record")}\n'
            mes += f'- Статья по экономическим преступлениям: {data.get("is_economic_criminal_record")}\n'
    mes += f'- Есть ли у вас исполнительное производство: {data.get("is_enforcement_proceedings")}\n' + \
            f'- Ваша официальная зарплата: {data.get("salary")} руб/мес.\n' + \
            f'- Являетесь ли вы зарплатником какого-либо банка: {data.get("is_bank_salary_employee")}\n' + \
            f'- Ваш возраст: {data.get("age")} лет\n' + \
            f'- Раньше уже брали кредит/ипотеку: {data.get("is_credit_earlier")}\n' + \
            f'- Был ли отказ в одобрении кредита/ипотеки: {data.get("is_credit_earlier_fail")}\n' + \
            f'- Планируемый вид кредита: {data.get("credit_type")}\n' + \
            f'- Ваш телеграм: {data.get("username")}\n' + \
            f'- Ваш телефон: {data.get("phone_number")}\n' + \
            f'(Нажмите одну из кнопок в всплывающем меню)'
    return mes

user_router = Router()


@user_router.message(F.text, Form.name)
async def state_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer('Для связи с вами нам необходим ваш номер телефона. Рекомендуем оставить свой номер телефона, так наш менеджер быстрее с вами свяжется и поможет в вашем вопросе!\n\n(Нажмите кнопку в всплывающем меню или напишите ответ)', reply_markup=kb_phone_number)
    await state.set_state(Form.phone_number)


@user_router.message(F.text, Form.phone_number)
async def state_phone_number(message: Message, state: FSMContext):
    if message.text == "🔙Назад":
        await message.answer('Введите ваше имя:', reply_markup=ReplyKeyboardRemove())
        await state.set_state(Form.name)
    else:
        username = message.from_user.username
        if username == None:
            await state.update_data(username="Не указан")
        else:
            await state.update_data(username=f'@{username}')
        if message.text == "Пропустить":
            

            tid = 99501534               # Номер счетчика
            cid = message.from_user.id   # Идентификатор ClientID
            ea = "skip_phone_number"     # Идентификатор счетчика
            await get_requests(tid, cid, ea)

            
            await state.update_data(phone_number="Не указан")
        else:
            await state.update_data(phone_number=message.text)
        await message.answer('Регион, где планируете взять потребительский кредит/ипотеку?\n\n(Напишите ответ)', reply_markup=kb_back)
        await state.set_state(Form.region)


@user_router.message(F.text, Form.region)
async def state_region(message: Message, state: FSMContext):
    if message.text == "🔙Назад":
        await message.answer('Для связи с вами нам необходим ваш номер телефона. Рекомендуем оставить свой номер телефона, так наш менеджер быстрее с вами свяжется и поможет в вашем вопросе!\n\n(Нажмите кнопку в всплывающем меню или напишите ответ)', reply_markup=kb_phone_number)
        await state.set_state(Form.phone_number)
    else:
        await state.update_data(region=message.text)
        await message.answer('Есть ли у вас судимость?\n\n(Нажмите одну из кнопок в всплывающем меню)', reply_markup=kb_yn)
        await state.set_state(Form.criminal_record)


@user_router.message(F.text, Form.criminal_record)
async def state_criminal_record(message: Message, state: FSMContext):
    if message.text == "🔙Назад":
        await message.answer('Регион, где планируете взять потребительский кредит/ипотеку?\n\n(Напишите ответ)', reply_markup=kb_back)
        await state.set_state(Form.region)
    else:
        await state.update_data(criminal_record=message.text)
        if message.text == "❌Нет":


            tid = 99501534               # Номер счетчика
            cid = message.from_user.id   # Идентификатор ClientID
            ea = "criminal_record_no"    # Идентификатор счетчика
            await get_requests(tid, cid, ea)

            
            await state.update_data(is_criminal_record="")
            await state.update_data(end_of_the_criminal_record="")
            await state.update_data(is_economic_criminal_record="")
            await message.answer('Есть ли у вас исполнительное производство?\n\n(Нажмите одну из кнопок в всплывающем меню)', reply_markup=kb_yn)
            await state.set_state(Form.is_enforcement_proceedings)
        elif message.text == "✅Да":

            
            tid = 99501534               # Номер счетчика
            cid = message.from_user.id   # Идентификатор ClientID
            ea = "criminal_record_yes"    # Идентификатор счетчика
            await get_requests(tid, cid, ea)


            await message.answer('Судимость действующая?\n\n(Нажмите одну из кнопок в всплывающем меню)', reply_markup=kb_yn)
            await state.set_state(Form.is_criminal_record)


@user_router.message(F.text, Form.is_criminal_record)
async def state_is_criminal_record(message: Message, state: FSMContext):
    if message.text == "🔙Назад":
        await message.answer('Есть ли у вас судимость?\n\n(Нажмите одну из кнопок в всплывающем меню)', reply_markup=kb_yn)
        await state.set_state(Form.criminal_record)
    else:
        await state.update_data(is_criminal_record=message.text)
        if message.text == "✅Да":
            await state.update_data(end_of_the_criminal_record="")
            await state.update_data(is_economic_criminal_record="")
            await message.answer('Есть ли у вас исполнительное производство?\n\n(Нажмите одну из кнопок в всплывающем меню)', reply_markup=kb_yn)
            await state.set_state(Form.is_enforcement_proceedings)
        elif message.text == "❌Нет":
            await message.answer('В каком году она была погашена?\n\n(Напишите ответ)', reply_markup=kb_back)
            await state.set_state(Form.end_of_the_criminal_record)


@user_router.message(F.text, Form.end_of_the_criminal_record)
async def state_end_of_the_criminal_record(message: Message, state: FSMContext):
    if message.text == "🔙Назад":
        await message.answer('Есть ли у вас судимость?\n\n(Нажмите одну из кнопок в всплывающем меню)', reply_markup=kb_yn)
        await state.set_state(Form.criminal_record)
    else:
        tmp = re.findall(r'\d+', message.text)
        if tmp:
            await state.update_data(end_of_the_criminal_record=tmp[0])
            await message.answer('Статья по экономическим преступлениям?\n\n(Нажмите одну из кнопок в всплывающем меню)', reply_markup=kb_yn)
            await state.set_state(Form.is_economic_criminal_record)
        else:
            await message.answer('Некорректное значение, введите год числом!', reply_markup=kb_back)


@user_router.message(F.text, Form.is_economic_criminal_record)
async def state_is_economic_criminal_record(message: Message, state: FSMContext):
    if message.text == "🔙Назад":
        await message.answer('Есть ли у вас судимость?\n\n(Нажмите одну из кнопок в всплывающем меню)', reply_markup=kb_yn)
        await state.set_state(Form.criminal_record)
    else:
        if message.text == "✅Да" or message.text == "❌Нет":
            await state.update_data(is_economic_criminal_record=message.text)
            await message.answer('Есть ли у вас исполнительное производство?\n\n(Нажмите одну из кнопок в всплывающем меню)', reply_markup=kb_yn)
            await state.set_state(Form.is_enforcement_proceedings)


@user_router.message(F.text, Form.is_enforcement_proceedings)
async def state_is_enforcement_proceedings(message: Message, state: FSMContext):
    if message.text == "🔙Назад":
        await message.answer('Есть ли у вас судимость?\n\n(Нажмите одну из кнопок в всплывающем меню)', reply_markup=kb_yn)
        await state.set_state(Form.criminal_record)
    else:
        if message.text == "✅Да" or message.text == "❌Нет":
            await state.update_data(is_enforcement_proceedings=message.text)
            await message.answer('Какая у вас официальная заработная плата (... руб/мес)?\n\n(Напишите ответ)', reply_markup=kb_back)
            await state.set_state(Form.salary)


@user_router.message(F.text, Form.salary)
async def state_salary(message: Message, state: FSMContext):
    if message.text == "🔙Назад":
        await message.answer('Есть ли у вас исполнительное производство?\n\n(Нажмите одну из кнопок в всплывающем меню)', reply_markup=kb_yn)
        await state.set_state(Form.is_enforcement_proceedings)
    else:
        salary_arr_int = re.findall(r'\d+', message.text)
        if salary_arr_int:

            salary_int = ""
            for x in salary_arr_int:
                salary_int += x
            await state.update_data(salary=salary_int)
            await message.answer('Являетесь ли вы зарплатником какого-либо банка?\n\n(Нажмите одну из кнопок в всплывающем меню)', reply_markup=kb_2)
            await state.set_state(Form.is_bank_salary_employee)
        else:
            await message.answer('Некорректное значение, введите заработную плату числом!', reply_markup=kb_back)


@user_router.message(F.text, Form.is_bank_salary_employee)
async def state_is_bank_salary_employee(message: Message, state: FSMContext):
    if message.text == "🔙Назад":
        await message.answer('Какая у вас официальная заработная плата (... руб/мес)?\n\n(Напишите ответ)', reply_markup=kb_back)
        await state.set_state(Form.salary)
    else:
        if message.text == "✅Да" or message.text == "❌Нет" or message.text == "Пропустить":
            if message.text == "Пропустить":
                await state.update_data(is_bank_salary_employee="Не указано")
            else:
                await state.update_data(is_bank_salary_employee=message.text)
            await message.answer('Сколько вам полных лет?', reply_markup=kb_back)
            await state.set_state(Form.age)


@user_router.message(F.text, Form.age)
async def state_age(message: Message, state: FSMContext):
    if message.text == "🔙Назад":
        await message.answer('Являетесь ли вы зарплатником какого-либо банка?\n\n(Нажмите одну из кнопок в всплывающем меню)', reply_markup=kb_2)
        await state.set_state(Form.is_bank_salary_employee)
    else:
        tmp = re.findall(r'\d+', message.text)
        if tmp:
            await state.update_data(age=tmp[0])
            await message.answer('Ранее уже брали кредит/ипотеку?\n\n(Нажмите одну из кнопок в всплывающем меню)', reply_markup=kb_yn)
            await state.set_state(Form.is_credit_earlier)
        else:
            await message.answer('Некорректное значение, введите возраст числом!', reply_markup=kb_back)


@user_router.message(F.text, Form.is_credit_earlier)
async def state_is_credit_earlier(message: Message, state: FSMContext):
    if message.text == "🔙Назад":
        await message.answer('Сколько вам полных лет?', reply_markup=kb_back)
        await state.set_state(Form.age)
    else:
        if message.text == "✅Да" or message.text == "❌Нет":
            await state.update_data(is_credit_earlier=message.text)
            await message.answer('Был ли отказ в одобрении кредита/ипотеки?\n\n(Нажмите одну из кнопок в всплывающем меню)', reply_markup=kb_yn)
            await state.set_state(Form.is_credit_earlier_fail)


@user_router.message(F.text, Form.is_credit_earlier_fail)
async def state_is_credit_earlier_fail(message: Message, state: FSMContext):
    if message.text == "🔙Назад":
        await message.answer('Ранее уже брали кредит/ипотеку?\n\n(Нажмите одну из кнопок в всплывающем меню)', reply_markup=kb_yn)
        await state.set_state(Form.is_credit_earlier)
    else:
        if message.text == "✅Да" or message.text == "❌Нет":
            await state.update_data(is_credit_earlier_fail=message.text)
            await message.answer('Какой вид кредита планируете взять - потребительский/ипотека?\n\n(Напишите вид словами, потребительский или ипотека. Мы поймем)', reply_markup=kb_back)
            await state.set_state(Form.credit_type)


@user_router.message(F.text, Form.credit_type)
async def state_credit_type(message: Message, state: FSMContext):
    if message.text == "🔙Назад":
        await message.answer('Был ли отказ в одобрении кредита/ипотеки?\n\n(Нажмите одну из кнопок в всплывающем меню)', reply_markup=kb_yn)
        await state.set_state(Form.is_credit_earlier_fail)
    else:
        await state.update_data(credit_type=message.text)
        data = await state.get_data()
        username = message.from_user.username
        if username == None and data.get("phone_number") == "Не указан":
            await message.answer('К сожалению не удалось получить данные для связи с вами. Для решения вашего вопроса и связи с менеджером необходим ваш номер телефона. Разрешаете ли вы получить его?\n\n(Нажмите на кнопку "Поделиться" в всплывающем меню)', reply_markup=kb_get_phone_number)
            await state.set_state(Form.get_phone_number)
        else:
            mes = mes_form_maker(data)
            await message.answer(mes, reply_markup=kb_check_data)
            await state.set_state(Form.check_state)


@user_router.message(F.contact, Form.get_phone_number)
async def state_get_phone_number(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    await state.update_data(phone_number=phone)
    data = await state.get_data()
    mes = mes_form_maker(data)
    await message.answer(mes, reply_markup=kb_check_data)
    await state.set_state(Form.check_state)


@user_router.message(F.text, Form.check_state)
async def state_check_state(message: Message, state: FSMContext):
    if message.text == "🔙Назад":
        await message.answer('Какой вид кредита планируете взять - потребительский/ипотека?\n\n(Напишите вид словами, потребительский или ипотека. Мы поймем)', reply_markup=kb_back)
        await state.set_state(Form.credit_type)
    if message.text == "❌Заполнить заново":
        await message.answer('Запускаем заполнение анкеты с начала. \n\nВведите ваше имя:', reply_markup=ReplyKeyboardRemove())
        await state.set_state(Form.name)
    if message.text == "✅Все верно":
        user_id = message.from_user.id


        tid = 99501534               # Номер счетчика
        cid = user_id   # Идентификатор ClientID
        ea = "all_correct"    # Идентификатор счетчика
        await get_requests(tid, cid, ea)

        
        data = await state.get_data() #.get("user_data")
        # data.update({'is_change': True})
        # print("Из состояния", data)

        # Если у пользователя уже была анкета, то он ее не заполняет, а получает из БД.
        # Ниже как раз проверка на это дело
        if not data:
            data = await Service.user.get_user_info(user_id=user_id)
            data['is_change'] = False
        else:
            data['is_change'] = True

        # if "user_data" in data.keys():
        #     data = data.get("user_data")
        # else:
        #     data = data.get("user_data")
        # Эта переменная с информацией из анкеты передается в БД
        print("Уже после выбора из бд или из состояния", data)
        user_data = {
            'user_id': user_id,
            'name': data.get("name"),
            'region': data.get("region"),
            'criminal_record': data.get("criminal_record"),
            'is_criminal_record': data.get("is_criminal_record"),
            'end_of_the_criminal_record': data.get("end_of_the_criminal_record"),
            'is_economic_criminal_record': data.get("is_economic_criminal_record"),
            'is_enforcement_proceedings': data.get("is_enforcement_proceedings"),
            'salary': data.get("salary"),
            'is_bank_salary_employee': data.get("is_bank_salary_employee"),
            'age': data.get("age"),
            'is_credit_earlier': data.get("is_credit_earlier"),
            'is_credit_earlier_fail': data.get("is_credit_earlier_fail"),
            'credit_type': data.get("credit_type"),
            'username': data.get("username"),
            'phone_number': data.get("phone_number"),
            'completed': False,
            'number_completed': 0,
            'number_changes': data.get('number_changes') if data.get('number_changes') else 0,
            'date_last_change': datetime.now().date(),
            'is_change': data.get("is_change"),
        }

        if (data.get("criminal_record") == "❌Нет" and data.get("is_enforcement_proceedings") == "❌Нет" and int(data.get("salary")) > 85000 and 25 < int(data.get("age")) < 45):
            mes = 'Спасибо за прохождение анкеты!\n❗️ Предварительно введенные вами параметры удовлетворяют скоринговым моделям банка:\n' + \
                  '✅ Нет судимости\n' + \
                  '✅ Нет исполнительного производства\n' + \
                  '✅ Официальная заработная плата может соответствовать финансовой нагрузке\n'
            if data.get("is_bank_salary_employee") == "✅Да":
                mes += f'✅ Являетесь зарплатником банка\n'
            mes += '✅ Попадаете в возрастной диапазон, который соответствует меньшему проценту дефолтности\n' + \
                   '✅ А значит - есть шанс получить одобрение.\n\n' + \
                   '❗️ Однако для точного ответа этого недостаточно, так как необходимо проанализировать и другие параметры, которых намного больше\n\n' + \
                   '✍ В ближайшее время наш менеджер свяжется с вами для уточнения деталей. (Звонок менеджера абсолютно бесплатный).\n\n' + \
                   f'📞 Телефон для связи: {data.get("phone_number")}\n📱 Телеграм: {data.get("username")}\n\n' + \
                   'И, при вашем согласии, менеджер проведет консультацию по вашему вопросу. А также, ПОЛНЫЙ финансово-экономический анализ.\n(Стоимость консультации 2000 руб., длительность до 25 минут)'
            await message.answer(mes, reply_markup=ReplyKeyboardRemove())

            user_data['important_user'] = True
        else:
            mes = 'Спасибо за прохождение анкеты!\n❗️ Предварительно некоторые введенные вами параметры удовлетворяют скоринговым моделям банка:\n'
            if data.get("criminal_record") == "❌Нет":
                mes += '✅ Нет судимости\n'
            if data.get("is_enforcement_proceedings") == "❌Нет":
                mes += '✅ Нет исполнительного производства\n'
            if int(data.get("salary")) > 85000:
                mes += '✅ Официальная заработная плата может соответствовать финансовой нагрузке\n'
            if data.get("is_bank_salary_employee") == "✅Да":
                mes += '✅ Являетесь зарплатником банка\n'
            if 25 < int(data.get("age")) < 45:
                mes += '✅ Попадаете в возрастной диапазон, который соответствует меньшему проценту дефолтности\n'

            mes += '☑️ Но у вас:\n'
            if not 25 < int(data.get("age")) < 45:
                mes += '❌ Не попадаете в возрастной диапазон, который соответствует меньшему проценту дефолтности\n'
            if data.get("is_criminal_record") == "✅Да":
                mes += '❌ Есть действующая судимость\n'
            if data.get("is_enforcement_proceedings") == "✅Да":
                mes += '❌ Есть исполнительное производство\n'

            if data.get("is_criminal_record") == "❌Нет":
                if data.get("is_economic_criminal_record") == "✅Да":
                    mes += '❌ Была судимость по экономическим статьям\n'
                elif data.get("end_of_the_criminal_record") != 'Не указано':
                    if int(datetime.now().year) - int(data.get("end_of_the_criminal_record")) <= 5:
                        mes += '❌ Есть недавно погашенная судимость - поэтому скоринговый балл у вас будет низким\n'
                    if int(datetime.now().year) - int(data.get("end_of_the_criminal_record")) > 5:
                        mes += f'❌ Есть погашенная судимость {int(datetime.now().year) - int(data.get("end_of_the_criminal_record"))} лет назад, если за это время вы не брали кредиты - скоринговый балл у вас будет низким\n'

            if int(data.get("salary")) <= 85000:
                mes += '❌ Официальная заработная плата может не соответствовать финансовой нагрузке\n'
            if data.get("is_bank_salary_employee") == "❌Нет" or data.get("is_bank_salary_employee") == "Не указано":
                mes += '❌ Вы не являетесь зарплатником банка\n'
            if int(data.get("salary")) < 25 and int(data.get("salary")) > 45:
                mes += '❌ Вы не попадаете в возрастной диапазон, который соответствует меньшему проценту дефолтности\n'

            mes += '🔴 А значит, есть вероятность отказа вашей заявки.\n\n' + \
                   '❗️ Однако для точного ответа этого недостаточно, так как необходимо проанализировать и другие параметры, которых намного больше.\n\n' + \
                   '✍ В ближайшее время наш менеджер свяжется с вами для уточнения деталей. (Звонок менеджера абсолютно бесплатный).\n\n' + \
                   f'📞 Телефон для связи: {data.get("phone_number")}\n📱 Телеграм: {data.get("username")}\n\n' + \
                   'И, при вашем согласии, менеджер проведет консультацию по вашему вопросу. А также, ПОЛНЫЙ финансово-экономический анализ.\n(Стоимость консультации 2000 руб., длительность до 25 минут)'
            await message.answer(mes, reply_markup=ReplyKeyboardRemove())

            user_data['important_user'] = False

        await state.update_data(user_data=user_data)

        # Переходим к оценке бота
        await message.answer('ДЛЯ ЗАВЕРШЕНИЯ РАБОТЫ НЕОБХОДИМО - оценить работу бота и оставить отзыв.\n\nПосле Вы получите сообщение о завершении работы.\n\n(Нажмите одну из кнопок в всплывающем меню)',
                             reply_markup=kb_3)
        await state.set_state(Form.mark)


@user_router.message(F.text, Form.mark)
async def state_mark(message: Message, state: FSMContext):
    if message.text == "Понравилось 👍" or message.text == "Не понравилось 👎":

        
        user_id = message.from_user.id
        if message.text == "Понравилось 👍":
            tid = 99501534               # Номер счетчика
            cid = user_id   # Идентификатор ClientID
            ea = "good"    # Идентификатор счетчика
            await get_requests(tid, cid, ea)
        if message.text == "Не понравилось 👎":
            tid = 99501534               # Номер счетчика
            cid = user_id   # Идентификатор ClientID
            ea = "bad"    # Идентификатор счетчика
            await get_requests(tid, cid, ea)

        
        print(await state.get_data())
        await state.update_data(mark=message.text)
        await message.answer('При желании - можете написать ваши рекомендации (что можно улучшить в работе нашего бота):\n\n(Нажмите одну из кнопок в всплывающем меню)', reply_markup=kb_4)
        await state.set_state(Form.is_feedback)


@user_router.message(F.text, Form.is_feedback)
async def state_is_feedback(message: Message, state: FSMContext):
    if message.text == "Оставить отзыв" or message.text == "Пропустить":
        await state.update_data(is_feedback=message.text)
        if message.text == "Оставить отзыв":
            await message.answer('Напишите ваш отзыв:', reply_markup=ReplyKeyboardRemove())
            await state.set_state(Form.feedback)
        if message.text == "Пропустить":
            await state.update_data(feedback="Не указан")
            data = await state.get_data()

            user_id = message.from_user.id
            user_id_in_db = await Service.user.user_exists(user_id=user_id)

            # Сохраняем анкету
            user_data = data.get("user_data")
            print(f"""
            ======================================
            Будем создавать пользователя:
            {user_data}
            ======================================
            """)

            print("======================================\n",
                  await Service.user.create_or_update_user(user_data=user_data),
                  "======================================\n")

            # Сохраняем отзыв
            mark = data.get("mark")
            feedback = data.get("feedback")
            await Service.user.save_feedback(user_id=user_id, mark=mark, feedback_text=feedback)

            # Проверяем необходимость уведомить менеджера о новом лиде
            if user_data['important_user'] and user_data["is_change"]:
                await start_mailing_to_managers(message, user_data["number_changes"])

            await message.answer('Спасибо, что воспользовались нашим ботом!\nУспехов в одобрении!', reply_markup=ReplyKeyboardRemove())
            await message.answer('Но это еще не все, ожидайте сообщение!\nНаш менеджер с Вами свяжется!', reply_markup=ReplyKeyboardRemove())
            await state.set_state(Form.approval)


@user_router.message(F.text, Form.feedback)
async def state_feedback(message: Message, state: FSMContext):
    await state.update_data(feedback=message.text)
    data = await state.get_data()

    user_id = message.from_user.id
    user_id_in_db = await Service.user.user_exists(user_id=user_id)

    # Сохраняем анкету
    user_data = data.get("user_data")
    await Service.user.create_or_update_user(user_data=user_data)

    # Сохраняем отзыв
    mark = data.get("mark")
    feedback = data.get("feedback")
    await Service.user.save_feedback(user_id=user_id, mark=mark, feedback_text=feedback)

    # Проверяем необходимость уведомить менеджера о новом лиде
    if user_data['important_user'] and user_data["is_change"]:
        await start_mailing_to_managers(message, user_data["number_changes"])

    await message.answer('Спасибо, что воспользовались нашим ботом!\nУспехов в одобрении!', reply_markup=ReplyKeyboardRemove())
    await message.answer('Но это еще не все, ожидайте сообщение!\nНаш менеджер с Вами свяжется!', reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.approval)


@user_router.callback_query(F.data.in_({"approval_agree", "approval_disagree"}))
async def handle_approval_callback(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    action = callback.data

    if action == "approval_agree":
        await state.update_data(approval='Согласен')
        await callback.message.answer("Ниже прикреплен QR-код для оплаты:", reply_markup=ReplyKeyboardRemove())
        await callback.message.answer_photo(photo=FSInputFile(QR_CODE_PATH))
        await callback.message.answer(
            "Ниже прикреплен файл инструкции. Нажмите на него, откройте у себя на телефоне и следуйте алгоритму.\n\n(Ссылка на сайт: https://credistory.ru/)",
            reply_markup=ReplyKeyboardRemove()
        )
        await callback.message.answer_document(document=FSInputFile(CREDIT_VERIFICATION_INSTRUCTIONS_PATH))
        await Service.user.update_approval(user_id=user_id)
        await Service.user.update_contract(user_id=user_id)

        await callback.message.answer(
            "Если вы еще не оставили отзыв или хотите дополнить имеющийся, просим вас это сделать. Ждем обратную связь!\n\n(Нажмите одну из кнопок в всплывающем меню)",
            reply_markup=kb_4
        )
        await state.set_state(Form.repeat_is_feedback)

    elif action == "approval_disagree":
        await state.update_data(approval='Не согласен')
        await callback.message.answer(
            "Без вашего согласия дальнейшая работа недоступна. Для продолжения необходимо согласиться с предыдущими положениями",
            reply_markup=kb_approval
        )
        await state.set_state(Form.approval)

    await callback.answer()  # Подтверждаем обработку колбека


@user_router.message(F.text, Form.repeat_is_feedback)
async def state_repeat_is_feedback(message: Message, state: FSMContext):
    if message.text == "Оставить отзыв" or message.text == "Пропустить":
        await state.update_data(repeat_is_feedback=message.text)
        if message.text == "Оставить отзыв":
            await message.answer('Напишите ваш отзыв:', reply_markup=ReplyKeyboardRemove())
            await state.set_state(Form.repeat_feedback)
        if message.text == "Пропустить":
            await state.update_data(repeat_feedback="Не указан")

            user_id = message.from_user.id
            repeat_feedback = "Не указан"
            await Service.user.save_repeat_feedback(user_id=user_id, repeat_feedback_text=repeat_feedback)

            await message.answer('Спасибо, что воспользовались нашим ботом!', reply_markup=ReplyKeyboardRemove())
            await state.clear()


@user_router.message(F.text, Form.repeat_feedback)
async def state_repeat_feedback(message: Message, state: FSMContext):
    await state.update_data(repeat_feedback=message.text)
    data = await state.get_data()

    user_id = message.from_user.id
    repeat_feedback = data.get("repeat_feedback")
    await Service.user.save_repeat_feedback(user_id=user_id, repeat_feedback_text=repeat_feedback)

    await message.answer('Спасибо, что воспользовались нашим ботом!', reply_markup=ReplyKeyboardRemove())
    await state.clear()
