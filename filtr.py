import pandas as pd
import numpy as np
import re

#gtm = pd.read_excel(r'C:\Users\nasty\Desktop\НТЦ\ГТМ.xlsx', header=[0, 1])
#history = pd.read_excel(r'C:\Users\nasty\Desktop\НТЦ\файл.xlsx', sheet_name='Данные')
def try_to_int(value):
    try:
        return int(value)
    except ValueError:
        return value

def history_processing(path1,path2):
    gtm = pd.read_excel(r'C:\Users\nasty\Desktop\НТЦ\ГТМ.xlsx', header=[0, 1])
    history = pd.read_excel(r'C:\Users\nasty\Desktop\НТЦ\файл.xlsx', sheet_name='Данные')
    history = history.fillna(0)

    unique_wells = history['№ скважины'].unique()
    history_new = pd.DataFrame()
    empty_wells = list()
    for i in unique_wells:
        slice = history.loc[history['№ скважины'] == i]
        # if any(slice["Время работы в добыче, часы"])!=0:
        if all(slice["Добыча нефти за посл.месяц, т"] == 0):
            empty_wells.append(i)
            #print("Скважина под номером " + str(i) + " удалена по причине простоя", end='\n')
            #print("")
        else:
            # while slice["Время работы в добыче, часы"].iloc[0]<600:
            while slice["Добыча нефти за посл.месяц, т"].iloc[0] == 0:
                slice = slice.iloc[1:]
            # while slice["Время работы в добыче, часы"].iloc[-1]<600:
            while slice["Добыча нефти за посл.месяц, т"].iloc[-1] == 0:
                slice = slice.iloc[:-1]
            history_new = history_new.append(slice, ignore_index=True)
            del slice
    unique_wells1 = history_new['№ скважины'].unique()
    unique_wells1_str = list(map(str, unique_wells1))

    yy = list()
    zz = list()
    for x in empty_wells:
        if isinstance(x, str) == True:
            regexPattern = r'(?=\-)''|''(?<=Л)'
            y = re.split(regexPattern, x)
            yy.append((y[0]))

            if (len(y) >= 2) and (len(y[1]) == 1):
                string = " ".join(map(str, unique_wells1))
                pattern = r'\b{}\d?'.format(y[0])
                z = re.findall(pattern, string)
                zz.extend(z)
    yy_int = list(map(try_to_int, yy))
    side_wells= list((set(unique_wells1) & set(yy_int)) | set(zz))
    unique_wells2 = list(set(unique_wells1) - set(side_wells))

    unique_wells3 = list()
    wells_LittleHours =list()
    for i in unique_wells2:
        slice = history_new.loc[history_new['№ скважины'] == try_to_int(i)]
        slice2 = slice[slice["Время работы, часы"]>500]
        if len(slice2)<12:
            wells_LittleHours.append(i)
            #print(str(i)+" мало проработала ")
        else:
            unique_wells3.append(i)

    unique_wells3 = list(map(str, unique_wells3))
    wells = gtm['Общее', 'Скважина'].unique()
    wells_with_gtm = list(set(wells) & set(unique_wells3))
    wells_normal = list(set(unique_wells3) - set(wells_with_gtm))
    wells_zbs = list()
    wells_zbs_with_grp = list()
    wells_with_grp = list()
    for i in wells_with_gtm:

        slice = history_new.loc[history_new['№ скважины'] == try_to_int(i)]
        data_init = slice["Дата"].iloc[0]

        slice1 = gtm.loc[gtm['Общее', 'Скважина'] == i]
        slice1 = slice1.sort_values(by=('Фактический ремонт', 'ВНР'), ignore_index=True)
        data = slice1['Фактический ремонт', 'ВНР'].loc[slice1['Общее', 'Тип'] == 'ГРП']
        r = slice1['Общее', 'Тип'].values.tolist()

        if '3БС' in r:
            if any(-31 * 24 * 3600 <= (elem - data_init).total_seconds() <= 12 * 31 * 24 * 3600 for elem in data):
                wells_zbs_with_grp.append(i)  # print(str(i)+" ЗБС с ГРП")
                continue
            elif all(-31 * 24 * 3600 >= (elem - data_init).total_seconds() for elem in data):
                wells_zbs.append(i)  # print(str(i)+' ЗБС без ГРП')
                continue
            else:
                wells_zbs_with_grp.append(i)
                wells_zbs.append(i)
                continue
        else:
            if all((elem - data_init).total_seconds() >= 12 * 31 * 24 * 3600 for elem in data):
                wells_normal.append(i)  # здесь все ГС
            else:
                wells_with_grp.append(i)
    wells_zbs.sort()
    wells_with_grp.sort()
    wells_normal.sort()
    wells_zbs_with_grp.sort()


    key = ['ГС без ГРП', 'ГС с ГРП', 'ЗБС без ГРП', 'ЗБС с ГРП']
    res = {'ГС без ГРП': wells_normal, 'ГС с ГРП': wells_with_grp, 'ЗБС без ГРП': wells_zbs, 'ЗБС с ГРП': wells_zbs_with_grp}
    return history_new, res

def create_dict(history_new):
    df_initial = history_new
    vr_v_dob = df_initial["Время работы, часы"].ravel()
    wells = df_initial["№ скважины"].ravel()
    neft = df_initial["Дебит нефти за последний месяц, т/сут"].ravel()
    data = df_initial["Дата"].ravel()

    wells_uniq =list(set(wells))# Список скважин
    uni = list(map(try_to_int,wells_uniq))
    # Создание словаря с данными по каждой скважине
    dict = {}
    for i in uni:
        dict[try_to_int(i)] = [[], [], [], []]
    for i in range(len(neft)):
        dict[wells[i]][0] += [neft[i]]
        dict[wells[i]][1] += [vr_v_dob[i]]
        dict[wells[i]][2] += [data[i]]
    return dict
