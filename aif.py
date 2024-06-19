# импорты
import streamlit as st  # это стримлит - библиотека, которое создает приложение
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
import yadisk
import os
import zipfile

# настройки
pd.set_option('display.max_columns', None)
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_style('whitegrid')
pio.templates.default = 'seaborn'


# переменные яндекс диска
app_id = '8771b2fc388945d49de1fb2baf9293f4'
secret_id = '60be4aaf6b0541dcb6cb3db7692f05e0'
ya_token = 'y0_AgAAAAApvuEnAAYAfQAAAADwkudoOCEmxONNR4Cq_OUWmJ6TOhh4iwE'

# меняем рабочую директорию на проект аиф
# os.chdir('/projects/aif/')

# титульный текст приложения
st.title('АиФ "Доброе сердце"')

# пишем функцию для загрузки файлов с яндекс диска
@st.cache_data(experimental_allow_widgets=True)  # эта строка дает кеширование - работает быстрее
def load_data() -> None:

    'Функция для загрузки файлов АиФ с яндекс диска'

    # подключаемся к диску и создаем список файлов для загрузки
    st.write('Подключаюсь к диску')
    y = yadisk.YaDisk(app_id, secret_id, ya_token)
    if y.check_token():
        st.write('Токен корректный')
    st.write('Найдены файлы для загрузки:')

    list_of_files = []  # переменная списка файлов
    
    # добавляем названия скачиваемых файлов в список загрузки
    for el in list(y.listdir('aif')):
        if el['path'].endswith('.csv'):
            list_of_files.append(el['path'])
    
    st.write(list_of_files)  # печатаем список в приложении

    # скачиваем файлы в директорию проекта
    for file in list_of_files:
        with st.spinner(f"Downloading {str(file.split('/')[-1])}"):
            y.download(file.split(':')[1], file.split('/')[-1])
        st.success(f"Done! {str(file.split('/')[-1])} loaded")

    list_of_dfs = [] # список в который мы загрузим три однотипных датасета 

    # загружаем датасеты в список
    for el in os.listdir():
        if 'dobro' in el:
            list_of_dfs.append(pd.read_csv(el, sep=';', encoding='utf8'))

    # сливаем датасеты в один общий
    final = pd.concat(list_of_dfs)

    # меняем названия колонок
    final.columns = ['customer_action_id',
            'action_template_name',
            'action_system_template_name', 'action_datetime',
            'action_datetime_utc', 'action_brand_system_name',
            'channel_id', 'channel_name',
            'external_channel_id',
            'channel_id_system_name',
            'channel_campaign', 'channel_utm_source',
            'utm_medium', 'utm_content',
            'utm_term', 'id_backend',
            'website_id',
            'user_id',
            'action_id',
            'template_sysname',
            'template_name',
            'mailing_action', 'mailing_name',
            'mailing_sysname', 'mailing_id',
            'mailing_varnum', 'mailing_link',
            'reason_not_sent',
            'reason_not_sent_name',
            'reason_sysname',
            'reason_name']
    final.to_csv('final.csv')

    # создаем архив zip
    with zipfile.ZipFile('final.zip', 'w') as myzip:
        myzip.write('final.csv')

    # добавляем кнопку скачать архив, который мы создали выше
    st.download_button(
    help='Архив файлов АиФ Доброе сердце',
    label="Скачать архив c объединным файлом :sunglasses:",
    data=open('final.zip', 'rb').read(),
    file_name='final.zip',
    mime='application/zip'
    )

# загружаем данные уже с директории приложения
channels = pd.read_csv('final.csv')
orders = pd.read_csv('paymentsaif.csv', sep=';', encoding='cp1251', usecols=[2, 3, 5, 17, 20, 21, 30])
orders.columns = ['order_datetime', 'channel_id', 'channel_name', 'order_aim', 'order_sum', 'order_status', 'user_id']
orders.order_datetime = pd.to_datetime(orders.order_datetime, dayfirst=True).dt.date
pays = orders[orders.order_status == 'Paid']

# создаем боковое меню
with st.sidebar:
    st.subheader("Выберите опцию") # заголовок меню
    download = st.sidebar.button(label='Download files from yadisk', type='primary') # кнопка загрузки
    direct_file_button = st.sidebar.button(label='Upload files for analysis')
    rfm_button = st.sidebar.button(label='RFM analysis') # кнопка РФМ
    channels = st.sidebar.button(label='Other staff') # кнопка когортного анализа
    # img_file_buffer = st.sidebar.button(label='make selfie') # эта кнопка захватывает изображение с камеры компа/ноута

# работа кнопки скачать: запускается функция загрузки файлов
if download:
    load_data()

# работа кнопки прямая загрузка файлов: загружаем файл через dropbox
if direct_file_button:
        uploaded_file = st.file_uploader('Загрузи файл для анализа')
        if uploaded_file is not None:
            orders = pd.read_csv(uploaded_file, sep=';', encoding='cp1251', usecols=[2, 3, 5, 17, 20, 21, 30])
            orders.columns = ['order_datetime', 'channel_id', 'channel_name', 'order_aim', 'order_sum', 'order_status', 'user_id']
            orders.order_datetime = pd.to_datetime(orders.order_datetime, dayfirst=True).dt.date
            pays = orders[orders.order_status == 'Paid']
            st.dataframe(orders.sample(5))

# работа кнопки РФМ: делаем РФМ анализ и выводим на экран основные моменты
if rfm_button:

    # выводим на экран количество счетов
    st.write(f'Всего оплаченных счетов: {pays.shape[0]}')
    st.write(f'Сумма оплаченных счетов: {pays.order_sum.sum():,} рублей')
    st.write(f'Средний чек: {pays.order_sum.sum()/ pays.shape[0]:.2f} рублей')
    min_date, max_date = pays.order_datetime.min(), pays.order_datetime.max()

    # бабахаем график
    pays_line = pays.groupby('order_datetime')['order_sum'].sum().reset_index()
    fig_sales = go.Figure()
    fig_sales.add_trace(go.Scatter(x=pays_line.order_datetime, 
                                   y=pays_line.order_sum, 
                                   name='сумма донаций',
                                   line=go.scatter.Line(color="lightslategrey")))
    fig_sales.add_trace(go.Scatter(x=pays_line.order_datetime, 
                                   y=pays_line.order_sum.rolling(15).mean(), 
                                   name='скользящее среднее', 
                                   line=go.scatter.Line(color="crimson",
                                                        width=3)))
    fig_sales.update_layout(title='Сумма донаций по дням, руб.', legend_orientation="h", legend=dict(x=.5, xanchor="center"))
    st.plotly_chart(fig_sales)

    st.markdown('### RFM анализ')
    # определяем период анализа
    st.write(f"Период анализа: с {min_date} по {max_date}, всего - {(max_date - min_date) / pd.Timedelta('1d')} дней")
    # определяем период жизни донаторов
    pays['period'] = (
    pays.groupby('user_id')['order_datetime']
    .transform(lambda cell: int((cell.max() - cell.min()) / pd.Timedelta('1d')) + 1)
    )

    # определяем дату анализа (максимальная дата + 1 день) и выводим на экран
    now = pays.order_datetime.max() + pd.Timedelta('1d')
    st.write(f'Дата отсчета для RFM анализа: {now}')
    
    # определяем РФМ значения
    pays['R_value'] = pays.order_datetime.apply(lambda cell: int(((now - cell) / pd.Timedelta('1d'))))
    pays['M_value'] = pays.groupby('user_id')['order_sum'].transform('sum')
    pays['F_value'] = pays.groupby('user_id')['user_id'].transform('count') / pays.period

    # создаем и печатаем боксплот для R
    fig_R_value = plt.figure(figsize=(12, 4))
    color_r = 'crimson'
    (
        plt.boxplot(x=pays.R_value, notch=True, vert=False,
                boxprops=dict(color=color_r),
                capprops=dict(color=color_r),
                whiskerprops=dict(color=color_r),
                flierprops=dict(color=color_r, markeredgecolor=color_r),
                medianprops=dict(color=color_r)
                ))
    plt.title('Распределение значений R-value')
    plt.ylabel('R_value')
    st.pyplot(fig_R_value)

    # бьем R на ранги
    r_bins = [0, 225, 547, pays.R_value.max()]
    r_labels = [3, 2, 1]
    pays['R'] = pd.cut(pays.R_value, bins=r_bins, labels=r_labels)
    st.write('Выбросы отсутствуют. Значения разделены на 3 ранга')

    # создаем и выводим на экран боксплот для F   
    fig_F_value = plt.figure(figsize=(12, 4))
    (
        plt.boxplot(x=pays.F_value, notch=True, vert=False,
                boxprops=dict(color=color_r),
                capprops=dict(color=color_r),
                whiskerprops=dict(color=color_r),
                flierprops=dict(color=color_r, markeredgecolor=color_r),
                medianprops=dict(color=color_r)
                ))
    plt.title('Распределение значений F-value')
    plt.ylabel('F_value')
    st.pyplot(fig_F_value)

    # бьем F на ранги
    f_bins = [0, .027, .11, pays.F_value.max()]
    f_labels = [1, 2, 3]
    pays['F'] = pd.cut(pays.F_value, bins=f_bins, labels=f_labels)
    st.write('Выбросы присутствуют. Значения очищены и разбиты на 3 ранга')

    # создаем и выводим на экран боксплот для M
    fig_M_value = plt.figure(figsize=(12, 4))
    (
        plt.boxplot(x=pays.M_value, notch=True, vert=False,
                boxprops=dict(color=color_r),
                capprops=dict(color=color_r),
                whiskerprops=dict(color=color_r),
                flierprops=dict(color=color_r, markeredgecolor=color_r),
                medianprops=dict(color=color_r)
                ))
    plt.title('Распределение значений M-value')
    plt.ylabel('M_value')
    st.pyplot(fig_M_value)

    # бьем М на ранги
    m_bins = [-0.1, 600, 2800, pays.M_value.max()]
    m_labels = [1, 2, 3]
    pays['M'] = pd.cut(pays.M_value, bins=m_bins, labels=m_labels)
    st.write('Выбросы присутствуют. Значения очищены и разбиты на 3 ранга')

    # Сцеплаем ранги в общий ранг RFM
    pays['RFM'] = pays.R.astype('str') + pays.F.astype('str') + pays.M.astype('str')

    # st.markdown позволяет выводить текст с разметкой как в юпитере
    st.markdown('**Описание сегментов**')
    st.markdown('''
                Итого получаем таблицу с идентификаторами пользователя и сегментом (просьба заказчика). Метрики расчитывались следующим образом: 1 - плохо, 2 - терпимо, 3 - хорошо   
**R:** **1** - был давно (больше 546 дней), **2** - не заходил от 225 до 546 дней, **3** - был недавно (не более 225 дней с момента визита  
**F:** **1** - заходит не часто (не более 1 раза за 38 дней), **2** - средняя активность(1 заход в течение 9 - 38 дней),  **3** - высокая активность (чаще 1 раза в 9 дней)   
**M:** **1** - жадные (до 600 рублей за все время), **2** - средняя сумма (600-2800 рублей), **3** - щедрые (более 2800 рублей)
                ''')
    st.markdown('''
|R - recency|F - frequency|M - monetary|
|:--|:--|:--|
|Время отсутствия|Частота заходов|Количество денег|
|**1** - был более 546 дней назад|**1** - заходит не чаще 0.027 раз в день|**1** - заплатил менее 600 рублей за все время|
|**2** - был от 546 до 225 дней назад|**2** - заходит от 0.027 до 0.11 раз в день|**2** - заплатил от 600 до 2800 рублей за все время|
|**3** - был менее 225 дней назад|**3** - заходит чаще 0.11 раз в день|**3** - заплатил более 2800 рублей за все время|
''')

    # готовим таблицу для RFM сегментов    
    rfm_stats = pays.groupby('RFM').agg({'user_id':'nunique', 'order_sum': ['count', 'mean', 'sum']}).reset_index()
    
    rfm_stats.columns = ['RFM сегмент', 'Человек в сегменте, чел.',
                     'Количество пожертвований, ед.', 'Среднее пожертвование, руб.',
                     'Сумма пожертвований, руб.']
    rfm_stats['test'] = rfm_stats['Сумма пожертвований, руб.']

    st.write('---')
  
    test_df = pays[['order_datetime', 'order_sum', 'user_id', 'RFM']]
    test_df['period'] = pd.to_datetime(test_df.order_datetime).dt.to_period('M')
    test_df = test_df.groupby(['RFM', 'period'])['order_sum'].sum().reset_index()
    test_df = test_df.sort_values(by='period')
    
    rfm_stats = rfm_stats.merge(test_df.groupby('RFM')['order_sum'].apply(list).reset_index(), left_on='RFM сегмент', right_on='RFM')
    rfm_stats = rfm_stats.drop(columns=['RFM'])
    # выводим на экран итоговую таблицу
    st.data_editor(rfm_stats.set_index('RFM сегмент').style.format(thousands=',', decimal='.', precision=2).background_gradient(cmap='Blues'),
                   column_config={
        "test": st.column_config.ProgressColumn(  # этот код делает правую колонку с прогресс баром
            "Сумма донаций",
            help="Общая сумма донаций",
            format="%f руб.",
            min_value=0,
            max_value=rfm_stats.test.max(),
        ),
        "order_sum": st.column_config.BarChartColumn(
            "Платежи по месяцам",
            help="The sales volume in the last 6 months",
            y_min=0,
            y_max=500000,
        ),
        'RFM сегмент': st.column_config.TextColumn(width='small'), # этот код и ниже уменьшает ширину колонок
        'Человек в сегменте, чел.': st.column_config.NumberColumn(width='small'), # почитаейте про stramlit column_config
        'Количество пожертвований, ед.': st.column_config.NumberColumn(width='small'), # шикарнейший инструмент для кастомизации
        'Среднее пожертвование, руб.': st.column_config.NumberColumn(width='small'),
        'Сумма пожертвований, руб.': st.column_config.NumberColumn(width='small'),
    },
    hide_index=True, height=980)

# этот код делает когортный анализ
# его вы напишите сами по аналогии с РФМ выше
if channels:
    st.write(channels.columns)

# если раскоментировать код ниже
# у вас появится кнопка для захвата изображения с камеры
# селфи сделать для портфолио
# if img_file_buffer:
#     my_photo = st.camera_input("Take a picture")
#     if my_photo is not None:
#     # To read image file buffer as bytes:
#     # bytes_data = my_photo.getvalue()
#     # Check the type of bytes_data:
#     # Should output: <class 'bytes'>
#     # st.write(type(bytes_data))
#         st.image(my_photo)
