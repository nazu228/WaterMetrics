"""
Модуль работы с Excel (openpyxl) для WaterMetrics.
Парсинг, динамическое обновление заголовков (+1 месяц) с корректным регистром ("ЗА ИЮЛЬ 2026 ГОДА"),
корректный сдвиг показаний (Новые_Предыдущие = Старые_Текущие),
профессиональное форматирование итоговой таблицы, 100% соответствие стилям исходника (Tahoma 8.5 pt, A...:M... подпись).
"""
import os
import re
from copy import copy
from datetime import datetime
import openpyxl
from openpyxl.cell.cell import Cell, MergedCell
from openpyxl.styles import Font, Border, Side, Alignment, PatternFill
from openpyxl.utils import get_column_letter

MONTHS_RU = ["январь", "февраль", "март", "апрель", "май", "июнь", "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"]
MONTHS_RU_GEN = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
MONTHS_RU_UPPER = ["ЯНВАРЬ", "ФЕВРАЛЬ", "МАРТ", "АПРЕЛЬ", "МАЙ", "ИЮНЬ", "ИЮЛЬ", "АВГУСТ", "СЕНТЯБРЬ", "ОКТЯБРЬ", "НОЯБРЬ", "ДЕКАБРЬ"]


class ExcelManager:
    @staticmethod
    def normalize_name(name):
        return re.sub(r'\s+', ' ', str(name or '').strip().lower())

    @staticmethod
    def parse_float_safe(val, default=None):
        """
        Безопасное преобразование значения ячейки (int, float, str с запятой/точкой, None) в float.
        Предотвращает TypeError / ValueError при работе со свежими/пустыми шаблонами.
        """
        if val is None:
            return default
        s = str(val).strip().replace(',', '.')
        if not s:
            return default
        try:
            return round(float(s), 3)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def clone_cell_style(src_cell, dst_cell):
        """Копирование всех стилей ячейки из шаблона."""
        if src_cell.has_style:
            dst_cell.font = copy(src_cell.font)
            dst_cell.border = copy(src_cell.border)
            dst_cell.fill = copy(src_cell.fill)
            dst_cell.number_format = copy(src_cell.number_format)
            dst_cell.alignment = copy(src_cell.alignment)

    @staticmethod
    def parse_house_and_next_month(template_path):
        """Извлекает имя объекта из 2-й строки шаблона и формирует название итогового файла."""
        try:
            wb = openpyxl.load_workbook(template_path, data_only=True)
            ws = wb.active
            row2_text = ""
            for col in range(1, 10):
                val = ws.cell(row=2, column=col).value
                if val:
                    row2_text = str(val).strip()
                    break

            house_str = "Отчет"
            match = re.search(r'(?:по\s+дому|по\s+адресу|объект|дом|ул\.)\s*:?\s*([А-Яа-я0-9\s\-\.,]+?\d+\s*[а-яА-Я]?)', row2_text, re.IGNORECASE)
            if match:
                house_str = match.group(1).strip(',. ')
            else:
                m_alt = re.search(r'([А-Яа-я0-9\s\-]+?\d+\s*[а-яА-Я]?)', row2_text)
                if m_alt:
                    house_str = m_alt.group(1).strip(',. ')

            row2_clean = re.sub(r'\s+', '', row2_text.lower())
            house_clean = re.sub(r'\s+', '', house_str.lower())

            special_keys = ["гассия6а", "аверкиева38", "посадского42"]
            is_special = any(k in row2_clean or k in house_clean for k in special_keys)

            if is_special:
                if not house_str.lower().endswith(" юд"):
                    final_name = f"{house_str} ЮД"
                else:
                    final_name = house_str
            else:
                final_name = house_str

            return f"{final_name}.xlsx"
        except Exception:
            return "Готово.xlsx"

    def _update_header_and_sheet_name(self, wb, ws):
        """Автоматическая смена месяца в имени листа, 1-й строке (Именительный падеж) и 2-й строке."""
        sheet_title = ws.title
        m_sheet = re.search(r'(\d{2})\.(\d{4})', sheet_title)

        if m_sheet:
            m, y = int(m_sheet.group(1)), int(m_sheet.group(2))
            next_m = 1 if m == 12 else m + 1
            next_y = y + 1 if m == 12 else y
        else:
            now = datetime.now()
            next_m = now.month
            next_y = now.year

        ws.title = f"{next_m:02d}.{next_y}"
        month_nom_upper = MONTHS_RU_UPPER[next_m - 1]

        # 1. Заголовок (1-я строка) — Именительный падеж ("ЗА ИЮЛЬ 2026 ГОДА")
        row1_cell = None
        for col in range(1, 15):
            val = ws.cell(row=1, column=col).value
            if val and str(val).strip():
                row1_cell = ws.cell(row=1, column=col)
                break

        if row1_cell:
            val_str = str(row1_cell.value)
            if re.search(r'ЗА\s+.*?\s+ГОДА', val_str, re.IGNORECASE):
                row1_cell.value = re.sub(
                    r'ЗА\s+.*?\s+ГОДА',
                    f'ЗА {month_nom_upper} {next_y} ГОДА',
                    val_str,
                    flags=re.IGNORECASE
                )
            elif re.search(r'ЗА\s+\[МЕСЯЦ\]\s+\[ГОД\]', val_str, re.IGNORECASE):
                row1_cell.value = re.sub(
                    r'ЗА\s+\[МЕСЯЦ\]\s+\[ГОД\]',
                    f'ЗА {month_nom_upper} {next_y}',
                    val_str,
                    flags=re.IGNORECASE
                )
            else:
                row1_cell.value = f"РЕЕСТР ТЕКУЩИХ И ПРЕДЫДУЩИХ ПОКАЗАНИЙ ИПУ ХОЛОДНОЙ И ГОРЯЧЕЙ ВОДЫ ЗА {month_nom_upper} {next_y} ГОДА В РАЗРЕЗЕ КАЖДОГО ЛИЦЕВОГО СЧЕТА"

        # 2. Подзаголовок (2-я строка)
        if m_sheet:
            row2_cell = None
            for col in range(1, 10):
                if ws.cell(row=2, column=col).value:
                    row2_cell = ws.cell(row=2, column=col)
                    break

            if row2_cell and row2_cell.value:
                val_str = str(row2_cell.value)
                old_m_idx = m - 1
                old_m_name = MONTHS_RU[old_m_idx]
                old_m_gen = MONTHS_RU_GEN[old_m_idx]
                new_m_name = MONTHS_RU[next_m - 1]
                new_m_gen = MONTHS_RU_GEN[next_m - 1]

                val_str = re.sub(old_m_name, new_m_name, val_str, flags=re.IGNORECASE)
                val_str = re.sub(old_m_gen, new_m_gen, val_str, flags=re.IGNORECASE)
                val_str = re.sub(str(y), str(next_y), val_str)
                row2_cell.value = val_str

    @staticmethod
    def _parse_meters(ws, detail_row, col_entries):
        def detect_water_type_from_text(text):
            if not text: return None
            s = str(text).lower()
            if 'гвс' in s or 'горячая' in s: return 'hot'
            if 'хвс' in s or 'холодная' in s: return 'cold'
            return None

        def get_cell_value_with_merged(ws_obj, r, c):
            val = ws_obj.cell(row=r, column=c).value
            if val is not None:
                return val
            for rng in ws_obj.merged_cells.ranges:
                if r in range(rng.min_row, rng.max_row + 1) and c in range(rng.min_col, rng.max_col + 1):
                    return ws_obj.cell(row=rng.min_row, column=rng.min_col).value
            return None

        def get_meter_info(group_cols, group_idx, search_rows=8):
            prev_c, curr_c, cons_c = group_cols
            water_type, meter_num = None, None
            start_row = max(1, detail_row - 1)
            end_row = max(1, detail_row - search_rows)

            min_col = prev_c
            max_col = cons_c

            for r in range(start_row, end_row - 1, -1):
                for c in range(min_col, max_col + 1):
                    val_str = str(get_cell_value_with_merged(ws, r, c) or '').strip()
                    if not val_str: continue
                    if water_type is None:
                        water_type = detect_water_type_from_text(val_str)
                    if meter_num is None:
                        for pat in [
                            r'(?:№|номер|счетчик|счётчик)\s*№?\s*(\d+)',
                            r'(\d+)\s*(?:№|номер|счетчик|счётчик)',
                            r'(?:холодная|горячая)\s*вода\s*№?\s*(\d+)',
                            r'(?:хвс|гвс)\s*№?\s*(\d+)',
                            r'сч[её]тчик\s*№?\s*(\d+)'
                        ]:
                            m = re.search(pat, val_str, re.IGNORECASE)
                            if m:
                                meter_num = int(m.group(1))
                                break
                if water_type is not None and meter_num is not None:
                    break

            if water_type is None:
                water_type = 'hot' if group_idx % 2 == 1 else 'cold'

            return water_type, meter_num

        groups = []
        i = 0
        while i + 2 < len(col_entries):
            if col_entries[i][1] == 'prev' and col_entries[i+1][1] == 'curr' and col_entries[i+2][1] == 'cons':
                groups.append((col_entries[i][0], col_entries[i+1][0], col_entries[i+2][0]))
                i += 3
            else:
                i += 1

        meters = []
        type_counter = {'cold': 0, 'hot': 0}
        for idx, cols in enumerate(groups):
            wtype, num = get_meter_info(cols, idx)
            if num is None:
                type_counter[wtype] += 1
                num = type_counter[wtype]
            else:
                type_counter[wtype] = max(type_counter.get(wtype, 0), num)
            meters.append({'type': wtype, 'num': num, 'cols': {'prev': cols[0], 'curr': cols[1], 'cons': cols[2]}})

        cold = sorted([m for m in meters if m['type'] == 'cold'], key=lambda m: m['cols']['prev'])
        hot = sorted([m for m in meters if m['type'] == 'hot'], key=lambda m: m['cols']['prev'])
        res = []
        for lst in (cold, hot):
            for i, m in enumerate(lst, 1):
                m['num'] = i
                res.append(m)
        return res

    def extract_apartments_and_meters(self, template_path, logger=None):
        """
        Извлечение структуры квартир и счетчиков.
        Используется сдвиг месяцев: стартовым значением ('prev') становится значение из колонки 'Текущие показания' прошлого месяца.
        """
        if logger:
            logger(f"ExcelManager.extract_apartments_and_meters: Извлечение из {template_path}", "INFO")
        try:
            wb = openpyxl.load_workbook(template_path, data_only=True)
            ws = wb.active

            detail_row = next((cell.row for row in ws.iter_rows(min_row=1, max_row=20, max_col=50)
                               for cell in row if cell.value and any(kw in str(cell.value).lower() for kw in ['предыдущее', 'текущее', 'расход'])), None)
            if not detail_row:
                if logger: logger("ExcelManager.extract_apartments_and_meters: Не найдена строка с показаниями", "ERROR")
                return {}

            col_entries = [(col, 'prev') if 'предыдущее' in str(ws.cell(row=detail_row, column=col).value or '').lower() else
                           (col, 'curr') if 'текущее' in str(ws.cell(row=detail_row, column=col).value or '').lower() else
                           (col, 'cons') for col in range(1, ws.max_column+1)
                           if any(kw in str(ws.cell(row=detail_row, column=col).value or '').lower() for kw in ['предыдущее', 'текущее', 'расход'])]

            meters = self._parse_meters(ws, detail_row, col_entries)
            name_col = next((col for col in range(1, 6) if ws.cell(row=detail_row, column=col).value is None), 1)

            result = {}
            in_closed_block = False

            for r in range(detail_row+1, ws.max_row+1):
                row_str = ' '.join(str(ws.cell(row=r, column=c).value or '') for c in range(1, 10)).strip().lower()
                name = str(ws.cell(row=r, column=name_col).value or '').strip()
                norm_name = self.normalize_name(name)

                if 'итого' in row_str or 'итого' in norm_name:
                    break

                if not name:
                    if in_closed_block:
                        in_closed_block = False
                    continue

                if re.search(r'(?:закрытые|замен[её]нные)\s*(?:сч[её]тчики|ипу)', norm_name) or re.search(r'(?:закрытые|замен[её]нные)\s*(?:сч[её]тчики|ипу)', row_str):
                    in_closed_block = True
                    continue

                if in_closed_block:
                    continue

                if any(ex in norm_name for ex in ['всего', 'подвал', 'чердак', 'лестница', 'коридор']):
                    continue

                m_list = []
                for m in meters:
                    # Сдвиг месяцев: Новые_Предыдущие_Показания = Старые_Текущие_Показания
                    curr_cell = ws.cell(row=r, column=m['cols']['curr']).value
                    prev_cell = ws.cell(row=r, column=m['cols']['prev']).value
                    val_to_use = curr_cell if (curr_cell is not None and str(curr_cell).strip() != '') else prev_cell
                    val = ExcelManager.parse_float_safe(val_to_use)
                    m_list.append({'type': m['type'], 'num': m['num'], 'prev': val})
                result[norm_name] = m_list

            if logger:
                logger(f"ExcelManager.extract_apartments_and_meters: Найдено {len(result)} квартир", "INFO")
            return result
        except Exception as e:
            if logger:
                logger(f"ExcelManager.extract_apartments_and_meters Ошибка: {e}", "ERROR")
            return {}

    @staticmethod
    def get_template_column_widths(template_path):
        """Извлекает точные ширины столбцов и параметры форматирования из XML шаблона."""
        widths = {}
        default_width = None
        try:
            import zipfile
            import xml.dom.minidom
            with zipfile.ZipFile(template_path) as z:
                sheet_names = [n for n in z.namelist() if n.startswith('xl/worksheets/sheet') and n.endswith('.xml')]
                if sheet_names:
                    xml_data = z.read(sheet_names[0])
                    dom = xml.dom.minidom.parseString(xml_data)
                    for sf in dom.getElementsByTagName('sheetFormatPr'):
                        if sf.hasAttribute('defaultColWidth'):
                            try:
                                default_width = float(sf.getAttribute('defaultColWidth'))
                            except Exception:
                                pass
                    for col in dom.getElementsByTagName('col'):
                        min_col = int(col.getAttribute('min'))
                        max_col = int(col.getAttribute('max'))
                        width = float(col.getAttribute('width'))
                        for c in range(min_col, max_col + 1):
                            widths[c] = width
        except Exception:
            pass
        return widths, default_width

    def extract_data(self, template_path, arcus_path, logger=None):
        """
        Основной метод загрузки данных.
        Сдвиг месяцев: Значения из колонки 'Текущие показания' шаблона (прошлый месяц) становятся
        базовыми показаниями ('prev') для нового месяца для КАЖДОГО счетчика.
        """
        if logger:
            logger("ExcelManager.extract_data: Начало загрузки данных", "INFO")

        self.template_column_widths, self.template_default_col_width = self.get_template_column_widths(template_path)

        wb = openpyxl.load_workbook(template_path, data_only=True)
        ws = wb.active

        detail_row = next((cell.row for row in ws.iter_rows(min_row=1, max_row=20, max_col=50)
                           for cell in row if cell.value and any(kw in str(cell.value).lower() for kw in ['предыдущее', 'текущее', 'расход'])), None)
        if not detail_row:
            raise RuntimeError("Не найдена строка с показаниями в шаблоне.")

        col_entries = [(col, 'prev') if 'предыдущее' in str(ws.cell(row=detail_row, column=col).value or '').lower() else
                       (col, 'curr') if 'текущее' in str(ws.cell(row=detail_row, column=col).value or '').lower() else
                       (col, 'cons') for col in range(1, ws.max_column+1)
                       if any(kw in str(ws.cell(row=detail_row, column=col).value or '').lower() for kw in ['предыдущее', 'текущее', 'расход'])]

        meters = self._parse_meters(ws, detail_row, col_entries)
        meter_by_type = {'cold': [m for m in meters if m['type']=='cold'], 'hot': [m for m in meters if m['type']=='hot']}
        name_col = next((col for col in range(1, 6) if ws.cell(row=detail_row, column=col).value is None), 1)

        all_rows, non_apartment_rows = {}, set()
        in_closed_block = False

        for r in range(detail_row+1, ws.max_row+1):
            row_str = ' '.join(str(ws.cell(row=r, column=c).value or '') for c in range(1, 10)).strip().lower()
            name = str(ws.cell(row=r, column=name_col).value or '').strip()
            norm_name = self.normalize_name(name)

            if 'итого' in row_str or 'итого' in norm_name:
                break

            if not name:
                if in_closed_block:
                    in_closed_block = False
                continue

            if re.search(r'(?:закрытые|замен[её]нные)\s*(?:сч[её]тчики|ипу)', norm_name) or re.search(r'(?:закрытые|замен[её]нные)\s*(?:сч[её]тчики|ипу)', row_str):
                in_closed_block = True
                non_apartment_rows.add(r)
                continue

            if in_closed_block:
                non_apartment_rows.add(r)
                continue

            if any(ex in norm_name for ex in ['всего', 'подвал', 'чердак', 'лестница', 'коридор']):
                non_apartment_rows.add(r)
                continue

            ap = {
                'row': r, 'name': name, 'norm_name': norm_name,
                'prev': {}, 'consum': {},
                'orig_fact': {'cold': False, 'hot': False},
                'striked': {'cold': False, 'hot': False},
                'is_empty': {},
                'has_3dec': {}
            }

            # Сдвиг показаний для всех счетчиков абонента: Новые_Предыдущие = Старые_Текущие
            for m in meters:
                curr_cell = ws.cell(row=r, column=m['cols']['curr']).value
                prev_cell = ws.cell(row=r, column=m['cols']['prev']).value
                val_to_use = curr_cell if (curr_cell is not None and str(curr_cell).strip() != '') else prev_cell
                prev_val = ExcelManager.parse_float_safe(val_to_use)

                ap['prev'][(m['type'], m['num'])] = prev_val
                ap['consum'][(m['type'], m['num'])] = 0.0

            all_rows[norm_name] = ap

        # Загрузка данных расхода из файла Аркус
        wb_arc = openpyxl.load_workbook(arcus_path, data_only=True)
        ws_arc = wb_arc.active
        arc_detail = next((cell.row for row in ws_arc.iter_rows(min_row=1, max_row=20, max_col=50)
                           for cell in row if cell.value and any(kw in str(cell.value).lower() for kw in ['предыдущее', 'текущее', 'расход'])), None)

        arc_col_entries = [(col, 'prev') if 'предыдущее' in str(ws_arc.cell(row=arc_detail, column=col).value or '').lower() else
                           (col, 'curr') if 'текущее' in str(ws_arc.cell(row=arc_detail, column=col).value or '').lower() else
                           (col, 'cons') for col in range(1, ws_arc.max_column+1)
                           if any(kw in str(ws_arc.cell(row=arc_detail, column=col).value or '').lower() for kw in ['предыдущее', 'текущее', 'расход'])]

        arc_meters = self._parse_meters(ws_arc, arc_detail, arc_col_entries)

        template_to_arcus = {}
        for t_m in meters:
            key = (t_m['type'], t_m['num'])
            template_to_arcus[key] = next((a_m['cols'] for a_m in arc_meters if a_m['type'] == key[0] and a_m['num'] == key[1]), None)

        arc_name_col = next((col for col in range(1, 6) if ws_arc.cell(row=arc_detail, column=col).value is None), 1)
        for r in range(arc_detail+1, ws_arc.max_row+1):
            arc_name = self.normalize_name(ws_arc.cell(row=r, column=arc_name_col).value)
            if arc_name not in all_rows: continue
            ap = all_rows[arc_name]
            for key, arc_cols in template_to_arcus.items():
                if arc_cols:
                    cell_cons = ws_arc.cell(row=r, column=arc_cols['cons'])
                    cell_val = cell_cons.value

                    is_empty = (cell_val is None or str(cell_val).strip() == '')
                    ap['is_empty'][key] = is_empty

                    cell_str = str(cell_val).strip() if cell_val is not None else ''
                    has_3_decimals = False
                    if '.' in cell_str or ',' in cell_str:
                        parts = re.split(r'[\.,]', cell_str)
                        if len(parts) == 2 and len(parts[1]) == 3:
                            has_3_decimals = True

                    val = ExcelManager.parse_float_safe(cell_val, default=0.0)
                    if abs(round(val, 2) - val) > 1e-5:
                        has_3_decimals = True

                    ap['consum'][key] = val
                    ap['has_3dec'][key] = has_3_decimals

                    if val > 0.0001:
                        ap['orig_fact'][key[0]] = True
                    if cell_cons.font and cell_cons.font.strike:
                        ap['striked'][key[0]] = True
                else:
                    ap['consum'][key] = 0.0
                    ap['is_empty'][key] = True
                    ap['has_3dec'][key] = False

        if logger:
            logger(f"ExcelManager.extract_data: Загружено квартир: {len(all_rows)}", "INFO")
        return wb, ws, meters, meter_by_type, all_rows, non_apartment_rows, name_col

    def save_result(self, wb, ws, save_path, meters, all_rows, non_apartment_rows, name_col, closed_meters=None, new_meters=None):
        """
        Запись результатов с гарантированным созданием папок, выравниванием рамок и шрифтов (100% Tahoma 8.5 pt),
        профессиональным оформлением итоговой строки, блока 'Закрытые ИПУ' и подписью от колонки A до конца таблицы.
        """
        save_dir = os.path.dirname(os.path.abspath(save_path))
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)

        self._update_header_and_sheet_name(wb, ws)

        total_cols = max((m['cols']['cons'] for m in meters), default=ws.max_column)
        new_dict = {(nm.apartment, nm.water_type, nm.meter_num): nm.initial_reading for nm in (new_meters or [])}

        # 1. Запись основной таблицы (каждый счетчик получает свои новые предыдущие и текущие показания)
        for ap in all_rows.values():
            for m in meters:
                key = (m['type'], m['num'])
                pval = new_dict.get((ap['norm_name'], m['type'], m['num']), ap['prev'].get(key))
                if pval is not None:
                    pval = round(float(pval), 3)

                cons = round(float(ap['consum'].get(key, 0.0)), 3)

                cell_prev = ws.cell(row=ap['row'], column=m['cols']['prev'])
                cell_prev.value = pval

                cell_curr = ws.cell(row=ap['row'], column=m['cols']['curr'])
                cell_cons = ws.cell(row=ap['row'], column=m['cols']['cons'])

                if pval is None:
                    cell_curr.value = None
                    cell_cons.value = None
                    continue

                curr_val = round(pval + cons, 3)
                cell_curr.value = curr_val
                cell_cons.value = cons

                p_font = cell_prev.font
                if p_font and p_font.strike:
                    nf = Font(name="Tahoma", size=8.5, strike=True, color=p_font.color)
                    cell_curr.font = nf
                    cell_cons.font = nf

        # 2. Физическое удаление старых служебных строк внутри диапазона квартир
        max_ap_row = max((ap['row'] for ap in all_rows.values()), default=5)
        intermediate_to_delete = [r for r in sorted(non_apartment_rows, reverse=True) if r <= max_ap_row]
        for r in intermediate_to_delete:
            ws.delete_rows(r)

        # Вычисляем точную последнюю строку квартир после удаления промежуточных строк
        last_ap_row = max_ap_row - len(intermediate_to_delete)

        # Безопасно очищаем объединенные ячейки ниже last_ap_row до удаления строк
        for range_ in list(ws.merged_cells.ranges):
            if range_.max_row > last_ap_row or range_.min_row > last_ap_row:
                try:
                    ws.unmerge_cells(str(range_))
                except Exception:
                    pass
                if range_ in ws.merged_cells.ranges:
                    try:
                        ws.merged_cells.ranges.remove(range_)
                    except Exception:
                        pass

        # Удаляем все старые строки ниже последней квартиры (старый блок закрытых ИПУ, старый Итого, старая подпись)
        if ws.max_row > last_ap_row:
            ws.delete_rows(last_ap_row + 1, ws.max_row - last_ap_row)

        cur_r = last_ap_row + 1

        # 3. Эталонные стили и цвета колонок напрямую из строки данных шаблона (строка 6)
        ref_row = 6 if ws.max_row >= 6 else (last_ap_row if last_ap_row > 0 else 1)
        col_fonts = {c: copy(ws.cell(row=ref_row, column=c).font) for c in range(1, total_cols + 1)}
        col_borders = {c: copy(ws.cell(row=ref_row, column=c).border) for c in range(1, total_cols + 1)}
        col_fills = {c: copy(ws.cell(row=ref_row, column=c).fill) for c in range(1, total_cols + 1)}
        col_num_fmts = {c: ws.cell(row=ref_row, column=c).number_format for c in range(1, total_cols + 1)}

        font_sig = Font(name="Tahoma", size=11.0, bold=False)

        align_left = Alignment(horizontal="left", vertical="center")
        align_right = Alignment(horizontal="right", vertical="center")
        align_center = Alignment(horizontal="center", vertical="center")

        # Вставка блока 'Закрытые ИПУ' (если они есть) с точными стилями колонок шаблона
        if closed_meters:
            ws.row_dimensions[cur_r].height = 17.25
            cell_hdr = ws.cell(row=cur_r, column=name_col)
            cell_hdr.value = "Закрытые ИПУ"
            if col_fonts.get(name_col):
                cell_hdr.font = copy(col_fonts[name_col])
            cell_hdr.alignment = align_left

            for c in range(1, total_cols + 1):
                cell = ws.cell(row=cur_r, column=c)
                if col_borders.get(c):
                    cell.border = copy(col_borders[c])
                if col_fonts.get(c):
                    cell.font = copy(col_fonts[c])
                if col_fills.get(c):
                    cell.fill = copy(col_fills[c])
                if c != name_col:
                    cell.value = None

            cur_r += 1

            grouped = {}
            for cm in closed_meters:
                grouped.setdefault(cm.apartment, []).append(cm)

            for apt_name, rec_list in grouped.items():
                ws.row_dimensions[cur_r].height = 17.25
                apt_display = apt_name.strip()
                if apt_display:
                    apt_display = apt_display[0].upper() + apt_display[1:]

                cell_name = ws.cell(row=cur_r, column=name_col)
                cell_name.value = apt_display
                if col_fonts.get(name_col):
                    cell_name.font = copy(col_fonts[name_col])
                cell_name.alignment = align_left
                if col_borders.get(name_col):
                    cell_name.border = copy(col_borders[name_col])

                for c in range(1, total_cols + 1):
                    cell = ws.cell(row=cur_r, column=c)
                    if col_fonts.get(c):
                        cell.font = copy(col_fonts[c])
                    if col_borders.get(c):
                        cell.border = copy(col_borders[c])
                    if col_fills.get(c):
                        cell.fill = copy(col_fills[c])
                    if col_num_fmts.get(c):
                        cell.number_format = col_num_fmts[c]
                    if c != name_col:
                        cell.alignment = align_right

                for cm in rec_list:
                    target_m = next((m for m in meters if m['type'] == cm.water_type and m['num'] == cm.meter_num), None)
                    if target_m:
                        fin_val = round(float(cm.final_reading), 3)
                        ws.cell(row=cur_r, column=target_m['cols']['prev']).value = fin_val
                        ws.cell(row=cur_r, column=target_m['cols']['curr']).value = fin_val
                        ws.cell(row=cur_r, column=target_m['cols']['cons']).value = 0.0

                cur_r += 1

        # 4. Оформление и пересчет сумм в единственной итоговой строке 'Итого' (1:1 стили и цвета шаблона)
        tot_r = cur_r
        ws.row_dimensions[tot_r].height = 15.0

        for c in range(1, total_cols + 1):
            cell = ws.cell(row=tot_r, column=c)
            cell.value = None
            if col_fonts.get(c):
                cell.font = copy(col_fonts[c])
            if col_borders.get(c):
                cell.border = copy(col_borders[c])
            if col_fills.get(c):
                cell.fill = copy(col_fills[c])
            if col_num_fmts.get(c):
                cell.number_format = col_num_fmts[c]
            if c != name_col:
                cell.alignment = align_right

        cell_tot_lbl = ws.cell(row=tot_r, column=name_col)
        cell_tot_lbl.value = "Итого"
        if col_fonts.get(name_col):
            cell_tot_lbl.font = copy(col_fonts[name_col])
        cell_tot_lbl.alignment = align_left

        for m in meters:
            sum_cons = round(sum(ap['consum'].get((m['type'], m['num']), 0.0) for ap in all_rows.values()), 3)
            ws.cell(row=tot_r, column=m['cols']['cons']).value = sum_cons

        # 5. Очистка устаревших объединенных ячеек и фантомных столбцов/строк
        for range_ in list(ws.merged_cells.ranges):
            if range_.max_row >= tot_r or range_.min_row >= tot_r:
                try:
                    ws.unmerge_cells(str(range_))
                except Exception:
                    pass
                if range_ in ws.merged_cells.ranges:
                    try:
                        ws.merged_cells.ranges.remove(range_)
                    except Exception:
                        pass

        if ws.max_column > total_cols:
            ws.delete_cols(total_cols + 1, ws.max_column - total_cols)

        # Форматирование 2-й строки: объединенная ячейка по ширине таблицы, выравнивание по центру.
        # 1-я строка не меняет форматирование.
        for range_ in list(ws.merged_cells.ranges):
            if range_.min_row == 2 and range_.max_row == 2:
                try:
                    ws.unmerge_cells(str(range_))
                except Exception:
                    pass
                if range_ in ws.merged_cells.ranges:
                    try:
                        ws.merged_cells.ranges.remove(range_)
                    except Exception:
                        pass
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=total_cols)
        ws.cell(row=2, column=1).alignment = align_center

        # 6. Динамическая подпись и очистка промежуточных строк
        sig_row = tot_r + 3

        # Очищаем промежуточные пустые строки от старых данных и границ
        for empty_r in range(tot_r + 1, sig_row):
            for c in range(1, total_cols + 1):
                cell = ws.cell(row=empty_r, column=c)
                cell.value = None
                cell.border = Border()
                cell.fill = PatternFill(fill_type=None)

        # Строка подписи
        for c in range(1, total_cols + 1):
            cell = ws.cell(row=sig_row, column=c)
            cell.value = None
            cell.border = Border()
            cell.fill = PatternFill(fill_type=None)

        sig_text = 'Директор ООО "Южный дом"  Бочарова В.М.               ___________________'

        sig_cell = ws.cell(row=sig_row, column=1)
        sig_cell.value = sig_text
        sig_cell.font = font_sig
        sig_cell.alignment = Alignment(horizontal="right", vertical="center")

        ws.merge_cells(start_row=sig_row, start_column=1, end_row=sig_row, end_column=total_cols)

        # Удаление фантомных строк исходного шаблона после строки подписи
        if ws.max_row > sig_row:
            ws.delete_rows(sig_row + 1, ws.max_row - sig_row)

        # 8. Гарантированное сохранение ширины колонок в точности как в исходном шаблоне
        if hasattr(self, 'template_column_widths') and self.template_column_widths:
            for col in range(1, total_cols + 1):
                col_letter = get_column_letter(col)
                if col in self.template_column_widths:
                    ws.column_dimensions[col_letter].width = self.template_column_widths[col]
                elif self.template_default_col_width:
                    ws.column_dimensions[col_letter].width = self.template_default_col_width

        try:
            wb.save(save_path)
        except PermissionError:
            base, ext = os.path.splitext(save_path)
            timestamp = datetime.now().strftime("%H%M%S")
            fallback_path = f"{base}_{timestamp}{ext}"
            wb.save(fallback_path)
            raise PermissionError(
                f"Файл '{os.path.basename(save_path)}' открыт в Excel! "
                f"Закройте файл в Excel и повторите попытку. (Файл сохранен как '{os.path.basename(fallback_path)}')"
            )