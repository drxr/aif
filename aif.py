# импорты
import streamlit as st  # библиотека, которое создает приложение
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# настройки
pd.set_option('display.max_columns', None)
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_style('whitegrid')
st.set_page_config(layout="wide")  # приложение во весь экран


# титульный текст приложения
st.title('АиФ "Доброе сердце"')

# создаем боковое меню
st.sidebar.subheader("Выберите опцию") # заголовок меню
uploaded_file_rfm = (st.sidebar.
                     file_uploader(label='Загрузите файлы c платежами для анализа (csv)', 
                                   type=['csv'])) # кнопка для аплоада файлов для рфм

rfm_button = st.sidebar.button('RFM анализ') # кнопка запуска рфм анализа

uploaded_file_channels = (st.sidebar.
                          file_uploader(label='Загрузите файлы c пользователями для анализа (xlsx)', 
                                        type=['xlsx'])) # кнопка для аплоада прочих файлов

# обработчик загрузки файлов для рфм    
if uploaded_file_rfm is not None:
    orders = pd.read_csv(uploaded_file_rfm, sep=';', 
                         encoding='cp1251', 
                         usecols=[2, 3, 5, 14, 15, 17, 20, 21, 30],
                         low_memory=False)
    
    orders.columns = ['order_datetime', 'channel_id', 'channel_name', 
                      'recurrent', 'repayment',
                      'order_aim', 'order_sum', 'order_status', 'user_id']
    
    orders.order_datetime = pd.to_datetime(orders.order_datetime, dayfirst=True).dt.date
    users = orders[['user_id', 'order_datetime']]
    st.write('Файл с платежами успешно загружен и обработан')
    st.write('Выберите период для анализа')

    # переменные слайдера дат
    MIN_MAX_RANGE = (orders.order_datetime.min(), orders.order_datetime.max())
    PRE_SELECTED_DATES = (orders.order_datetime.max() - pd.Timedelta('30d'), orders.order_datetime.max())

    # слайдер дат: выбор периода анализа
    selected_min, selected_max = st.slider(
    "Выбор границ анализируемого периода",
    value=PRE_SELECTED_DATES,
    step=timedelta(days=1),
    min_value=MIN_MAX_RANGE[0],
    max_value=MIN_MAX_RANGE[1],
    format="YYYY-MM-DD",  
)   
    
    # вшиваем даты слайдера в датасет
    orders = orders[(orders.order_datetime >= selected_min) & (orders.order_datetime <= selected_max)]
    pays = orders[orders.order_status == 'Paid']
    unpays = orders[orders.order_status == 'notpaid']
    fails = orders[orders.order_status == 'fail']


# работа кнопки РФМ: делаем РФМ анализ и выводим на экран основные моменты
if rfm_button:

    st.subheader('Общая информация')

    # выводим на экран количество счетов
    st.write(f'Всего оплаченных счетов: **{pays.shape[0]}**')
    st.write(f'Сумма оплаченных счетов: **{pays.order_sum.sum():,}** рублей')
    mean_pay = pays.groupby('order_datetime')['order_sum'].mean().reset_index()
    st.write(f'Средний чек: **{pays.order_sum.sum()/ pays.shape[0]:.2f}** рублей')

    # график динамики среднего чека
    fig_mean = px.line(mean_pay, x="order_datetime", y="order_sum", title='Динамика среднего дневного пожертвования, руб.')
    st.plotly_chart(fig_mean)

    # бабахаем график с динамикой платежей
    pays_line = pays.groupby('order_datetime')['order_sum'].sum().reset_index()

    fig_dinamics = go.Figure()
    fig_dinamics.add_traces(go.Scatter(x=pays_line.order_datetime, 
                                       y=pays_line.order_sum, 
                                       line=dict(color="lightgrey"),
                                       mode='lines', name = 'Платежи'))
    fig_dinamics.add_traces(go.Scatter(x=pays_line.order_datetime, 
                                       y=pays_line.order_sum.rolling(15).mean(), 
                                       line=dict(color="crimson", width=2),
                                       mode='lines', name = 'Платежи скользящее среднее'))
    fig_dinamics.update_layout(title_text="Динамика пожертвований по дням, руб.",
        legend=dict(yanchor="top",
                                  y=0.99,
                                  xanchor="left", x=0.01,
                                  orientation='h'))
    st.plotly_chart(fig_dinamics)
    st.write('---')

    pays['month'] = pd.to_datetime(pays.order_datetime).dt.to_period('M')
    month_pays = pays.groupby('month')['order_sum'].sum().reset_index()
    month_pays['month'] = month_pays.month.astype('str')
    fig_months = px.bar(month_pays, y='order_sum', x='month', text_auto='.2s',
            title="Помесячная сумма пожертвований, руб.")
    fig_months.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
    st.plotly_chart(fig_months)

    # рекуренты
    st.subheader('Информация о рекурентах')

    # выделяем рекурентов и не рекурентов
    recs = pays[pays.recurrent == True]
    unrecs = pays[pays.recurrent == False]

    # информация по платежам и количеству рекурентов
    st.write(f'Количество рекурентов за период: **{recs.user_id.nunique()}** человек')
    st.write(f'Сумма пожертвования рекурентов за период: **{recs.order_sum.sum():,}** рублей')
    st.write(f'Среднее пожертвование рекурентов за период: **{recs.order_sum.mean():,.2f}** рублей')
    
    # строим график по рекурентам
    fig_rec = make_subplots(rows=1, cols=2, specs=[[{'type':'domain'}, {'type':'domain'}]])
    fig_rec.add_trace(go.Pie(labels=['Рекурент', 'Не рекурент'], 
                                  values=[recs.order_sum.sum(), unrecs.order_sum.sum()], 
                                  name="В рублях"), 1, 1)
    fig_rec.add_trace(go.Pie(labels=['Рекурент', 'Не рекурент'], 
                                  values=[recs.order_sum.count(), unrecs.order_sum.count()], 
                                  name="Количество"), 1, 2)

    fig_rec.update_traces(hole=.6, hoverinfo="label+percent+name")

    fig_rec.update_layout(
        title_text="Доля рекурентов по количеству и платежам в общем объеме пожертвований",
        annotations=[dict(text='В рублях', x=0.16, y=0.5, font_size=20, showarrow=False),
                 dict(text='Количество', x=0.87, y=0.5, font_size=20, showarrow=False)])
    st.plotly_chart(fig_rec)
    st.write('---')

    # приток / отток
    st.subheader('Приток / отток благотворителей')
    active = (
        users[users.order_datetime >= (users.order_datetime.max() - pd.Timedelta('90d'))]
        ['user_id'].unique().tolist()
              )
    st.write(f' Количество активных пользователей: {len(active)} человек (делали платежи не позднее, чем 90 дней назад)')

    passive = (
        users[(users.order_datetime <= (users.order_datetime.max() - pd.Timedelta('90d'))) 
              & 
              (~users.user_id.isin(active))]['user_id'].tolist()
              )
    st.write(f'Отток за все время: {len(passive)} человек')
    users['year'] = pd.to_datetime(users.order_datetime).dt.year
    passive_2024 = users[(users.year == 2024) & (~users.user_id.isin(active))]
    st.write(f'Количество ушедших доноров, которые были активны в 2024 году: {passive_2024.user_id.nunique()} человек')

    def convert_df(df):
            # IMPORTANT: Cache the conversion to prevent computation on every rerun
            return df.to_csv().encode("utf-8")

    fresh_leavers = convert_df(passive_2024['user_id'])

    st.download_button(
            label="Скачать отток за 2024 год",
            data=fresh_leavers,
            file_name="left_2024_users.csv",
            mime="text/csv",
        )
    
    # Неоплаченные счета и сбои платежей
    st.subheader('Неоплаченные пожертвования и ошибки в платежах')
    st.write(f'Всего неоплаченных счетов: **{unpays.shape[0]}**')
    st.write(f'Сумма неоплаченных счетов: **{unpays.order_sum.sum():,}** рублей')
    st.write('---')
    st.write(f'Всего оплат с ошибкой: **{fails.shape[0]}**')
    st.write(f'Сумма оплат с ошибкой: **{fails.order_sum.sum():,}** рублей')
    min_date, max_date = pays.order_datetime.min(), pays.order_datetime.max()

    # График с ошибками в платежах
    fig_mistakes = make_subplots(rows=1, cols=2, specs=[[{'type':'domain'}, {'type':'domain'}]])
    fig_mistakes.add_trace(go.Pie(labels=['Оплачено', 'Не оплачено', 'Ошибка'], 
                                  values=[pays.order_sum.sum(), unpays.order_sum.sum(), fails.order_sum.sum()], 
                                  name="В рублях"), 1, 1)
    fig_mistakes.add_trace(go.Pie(labels=['Оплачено', 'Не оплачено', 'Ошибка'], 
                                  values=[pays.order_sum.count(), unpays.order_sum.count(), fails.order_sum.count()], 
                                  name="Количество"), 1, 2)

    fig_mistakes.update_traces(hole=.6, hoverinfo="label+percent+name")

    fig_mistakes.update_layout(
        title_text="Доля неоплаченных пожертвований и ошибок платежей",
        annotations=[dict(text='В рублях', x=0.16, y=0.5, font_size=20, showarrow=False),
                 dict(text='Количество', x=0.87, y=0.5, font_size=20, showarrow=False)])
    st.plotly_chart(fig_mistakes)

    st.markdown('### RFM анализ')
    if (selected_max - selected_min) / pd.Timedelta('1d') < 365:
        st.write('Для RFM анализа необходимо указать период от года')
    else:
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

        # бьем R на ранги
        r_bins = [0, 90, 365, pays.R_value.max()]
        r_labels = [3, 2, 1]
        pays['R'] = pd.cut(pays.R_value, bins=r_bins, labels=r_labels)

        # бьем F на ранги
        f_bins = [0, .027, .11, pays.F_value.max()]
        f_labels = [1, 2, 3]
        pays['F'] = pd.cut(pays.F_value, bins=f_bins, labels=f_labels)

        # бьем М на ранги
        m_bins = [-0.1, 600, 2800, pays.M_value.max()]
        m_labels = [1, 2, 3]
        pays['M'] = pd.cut(pays.M_value, bins=m_bins, labels=m_labels)

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
        rfm_stats['Человек в сегменте, чел.'] =  rfm_stats['Человек в сегменте, чел.'].astype('float')
        rfm_stats['Количество пожертвований, ед.'] = rfm_stats['Количество пожертвований, ед.'].astype('float')
        rfm_stats['Сумма пожертвований, руб.'] = rfm_stats['Сумма пожертвований, руб.'].astype('float')
        rfm_stats['test'] = rfm_stats['test'].astype('float')

        st.dataframe(rfm_stats.set_index('RFM сегмент'),
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
        },
        height=980)

        final = pays[['user_id', 'RFM']]

        def convert_df(df):
            # IMPORTANT: Cache the conversion to prevent computation on every rerun
            return df.to_csv().encode("utf-8")

        csv = convert_df(final)

        st.download_button(
            label="Скачать доноров с RFM сегментом",
            data=csv,
            file_name="rfm_users.csv",
            mime="text/csv",
        )

        
