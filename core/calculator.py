"""
Ядро расчетов WaterMetrics.
Реализация математических алгоритмов биллинговых систем расчёта объёмов водопотребления.
Соблюдение 3 Законов Человеческого Ввода, двухфазной синхронной динамики нормативов по жильцам,
защиты интерфейсов и E2E-автотестов (WaterCalculator, calculate, _apply_manual_correction).
"""
import random
import math
import copy
import traceback


class WaterCalculator:
    def __init__(self, config, logger_callback, confirm_callback):
        self.config = config
        self.log = logger_callback
        self.request_confirmation = confirm_callback

    # ==============================================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ И ПРЕДИКТОРЫ
    # ==============================================================================

    def _is_3dec_meter(self, ap, key):
        """Проверка, является ли счетчик начислением 'по среднему' из Аркуса (имеет 3 знака после запятой)."""
        if ap.get('has_3dec', {}).get(key, False):
            return True
        val = ap['consum'].get(key, 0.0)
        return abs(round(val, 2) - round(val, 3)) > 1e-5

    def _is_prev_fractional_meter(self, ap, key):
        """Проверка, были ли предыдущие показания счетчика дробными (например 142.35 или 54.7 м3)."""
        pval = ap.get('prev', {}).get(key)
        if pval is None:
            return False
        return abs(float(pval) - round(float(pval))) > 1e-5

    def _is_integer_meter(self, ap, key):
        """Проверка, является ли расход счетчика целым числом (1.0, 2.0, 3.0 и т.д. при val >= 0.2 м3)."""
        val = ap['consum'].get(key, 0.0)
        if val < 0.2:
            return False
        return abs(val - round(val)) < 1e-5

    def _is_fractional_meter(self, ap, key):
        """Проверка, является ли расход счетчика дробным (val >= 0.2 м3 и не целое)."""
        val = ap['consum'].get(key, 0.0)
        if val < 0.2:
            return False
        return not self._is_integer_meter(ap, key) or self._is_3dec_meter(ap, key) or self._is_prev_fractional_meter(ap, key)

    def _can_add_gvs(self, r_dict, n, m_cold, m_hot, amount, threshold=0.0):
        """Проверка физического лимита: Cons_HVS >= Cons_GVS - threshold."""
        cold_tot = sum(r_dict[n]['consum'].get((m['type'], m['num']), 0.0) for m in m_cold)
        hot_tot = sum(r_dict[n]['consum'].get((m['type'], m['num']), 0.0) for m in m_hot)
        return (cold_tot + threshold >= hot_tot + amount - 1e-5)

    def _can_sub_hvs(self, r_dict, n, m_cold, m_hot, amount, threshold=0.0):
        """Проверка физического лимита: Cons_HVS - amount >= Cons_GVS - threshold."""
        cold_tot = sum(r_dict[n]['consum'].get((m['type'], m['num']), 0.0) for m in m_cold)
        hot_tot = sum(r_dict[n]['consum'].get((m['type'], m['num']), 0.0) for m in m_hot)
        return (cold_tot - amount + threshold >= hot_tot - 1e-5)

    # ==============================================================================
    # РУЧНАЯ КОРРЕКТИРОВКА (ADD_HVS)
    # ==============================================================================

    def _apply_manual_correction(self, rows_dict, add_total, meters_list, norm_val, threshold=0.0):
        """
        Ручная корректировка ХВС (+ / -) с соблюдением 3 Законов Человеческого Ввода.
        Закон 1: Добавки к целым только целыми кубами (+1.0, +2.0, -1.0).
        Закон 2: Квартиры с нормативом и 0.0 м3 защищены (Закон "Каменных стен").
        Закон 3: Дробный остаток передается на дробные счетчики.
        """
        self.log(f"Начало ручной корректировки на {add_total:+.3f} м3", "INFO")
        if not meters_list:
            self.log("Нет счётчиков для ручной корректировки.", "ERROR")
            return False

        water_type = meters_list[0]['type']
        elig_pairs = []

        # Закон 2: Исключаем нормативы Этапа 1, зачеркнутые и малые расходы < 0.2 м3
        for n, ap in rows_dict.items():
            if 'квартира' not in ap['norm_name']:
                continue
            if ap['striked'].get(water_type, False):
                continue
            if ap.get('is_normative_stage1', False):
                continue
            if not ap['orig_fact'].get(water_type, False):
                continue

            for m in meters_list:
                key = (m['type'], m['num'])
                val = ap['consum'].get(key, 0.0)

                if val < 0.2:
                    continue

                if m['num'] == 1 and norm_val > 0:
                    ratio = val / norm_val
                    if abs(ratio - round(ratio)) < 0.001 and round(ratio) > 0:
                        continue

                elig_pairs.append((n, key))

        if not elig_pairs:
            self.log("Нет подходящих счётчиков для корректировки (расход равен 0, нормативу или < 0.2 м3).", "ERROR")
            return False

        m_cold = [m for m in meters_list if m['type'] == 'cold']
        m_hot = [m for m in meters_list if m['type'] == 'hot']

        if add_total > 0:
            rem = round(add_total, 3)
            int_add = int(math.floor(rem))
            frac_add = round(rem - int_add, 3)

            if int_add >= 1:
                rem_int = int_add
                idx = 0
                while rem_int >= 1 and elig_pairs:
                    n, key = elig_pairs[idx % len(elig_pairs)]
                    chunk = 1.0
                    rows_dict[n]['consum'][key] = round(rows_dict[n]['consum'].get(key, 0.0) + chunk, 3)
                    rem_int -= 1
                    idx += 1

            if frac_add > 0.0001:
                frac_pairs = [p for p in elig_pairs if self._is_prev_fractional_meter(rows_dict[p[0]], p[1]) or self._is_fractional_meter(rows_dict[p[0]], p[1])]
                target_p = frac_pairs[0] if frac_pairs else elig_pairs[0]
                rows_dict[target_p[0]]['consum'][target_p[1]] = round(rows_dict[target_p[0]]['consum'][target_p[1]] + frac_add, 3)

            self.log(f"Ручная корректировка +{add_total:.3f} м3 выполнена", "SUCCESS")
            return True
        else:
            req = round(abs(add_total), 3)
            int_req = int(math.floor(req))
            frac_req = round(req - int_req, 3)

            # При списании в минус приоритет отдаем 2-му и последующим счетчикам (m['num'] > 1)
            active_pairs = sorted(elig_pairs, key=lambda p: p[1][1] if isinstance(p[1], tuple) else 1, reverse=True)
            idx = 0

            if int_req >= 1:
                rem_int = int_req
                while rem_int >= 1 and active_pairs:
                    curr_idx = idx % len(active_pairs)
                    n, key = active_pairs[curr_idx]
                    cur = rows_dict[n]['consum'].get(key, 0.0)

                    if cur >= 1.2 and self._can_sub_hvs(rows_dict, n, m_cold, m_hot, 1.0, threshold):
                        rows_dict[n]['consum'][key] = round(cur - 1.0, 3)
                        rem_int -= 1
                        idx += 1
                    else:
                        active_pairs.pop(curr_idx)

            if frac_req > 0.0001 and active_pairs:
                for n, key in active_pairs:
                    cur = rows_dict[n]['consum'].get(key, 0.0)
                    if cur - frac_req >= 0.2 and self._can_sub_hvs(rows_dict, n, m_cold, m_hot, frac_req, threshold):
                        rows_dict[n]['consum'][key] = round(cur - frac_req, 3)
                        break

            self.log(f"Ручная корректировка -{abs(add_total):.3f} м3 выполнена", "SUCCESS")
            return True

    # ==============================================================================
    # ОСНОВНОЙ ПУБЛИЧНЫЙ МЕТОД РАСЧЕТА
    # ==============================================================================

    def calculate(self, all_rows, meters, meter_by_type):
        """
        Основной алгоритм расчёта объёмов с адаптивным циклом ослабления порога.
        Нормативы начисляются только на 1-й счетчик соответствующего типа (f_key_cold, f_key_hot).
        Сдвиг показаний производится корректно для ВСЕХ счетчиков каждого абонента.
        Нормативы 100% защищены (Закон 2) и никогда не получают дробных начислений.
        """
        closed_count = len(self.config.closed_meters or [])
        new_count = len(self.config.new_meters or [])

        # ==============================================================================
        # 1. ИНИЦИАЛИЗАЦИЯ ЦЕЛЕВЫХ ПЕРЕМЕННЫХ (ГАРАНТИЯ ОТ ОШИБКИ NameError)
        # ==============================================================================
        target_cold_val = round(float(self.config.target_cold), 3)
        target_hot_val = round(float(self.config.target_hot), 3)
        add_value = round(float(self.config.add_hvs), 3)

        expected_cold = target_cold_val
        expected_hot = target_hot_val

        self.log(
            f"Начало расчёта. Цель ХВС: {target_cold_val:.3f}, Цель ГВС: {target_hot_val:.3f}, "
            f"Коррекция: {add_value:.3f}",
            "INFO"
        )
        self.log(f"Нормативы: ХВС={self.config.norm_cold:.3f}, ГВС={self.config.norm_hot:.3f}", "INFO")
        self.log(f"Замены: закрытых {closed_count}, новых {new_count}", "INFO")

        NORM_COLD = round(float(self.config.norm_cold), 3)
        NORM_HOT = round(float(self.config.norm_hot), 3)

        m_cold = meter_by_type.get('cold', [])
        m_hot = meter_by_type.get('hot', [])

        # Нормативы всегда привязываются строго к ПЕРВОМУ счетчику (num = 1)
        f_key_cold = (m_cold[0]['type'], m_cold[0]['num']) if m_cold else None
        f_key_hot = (m_hot[0]['type'], m_hot[0]['num']) if m_hot else None

        # ==============================================================================
        # ЭТАП 1: ДВУХФАЗНОЕ СИНХРОННОЕ НАЧИСЛЕНИЕ НОРМАТИВОВ (ПО ЖИЛЬЦАМ)
        # ==============================================================================
        self.log("Этап 1: Двухфазное синхронное начисление нормативов на пустые квартиры", "INFO")

        def get_tgt_rem(r_dict, m_list, target):
            if not m_list:
                return 0.0
            sum_all = sum(ap['consum'].get((m['type'], m['num']), 0.0) for ap in r_dict.values() for m in m_list)
            return round(target - sum_all, 3)

        tgt_rem_cold = get_tgt_rem(all_rows, m_cold, target_cold_val)
        tgt_rem_hot = get_tgt_rem(all_rows, m_hot, target_hot_val)

        empty_apts = []
        for n, ap in all_rows.items():
            if 'квартира' not in ap['norm_name']:
                continue

            is_empty_c = all(ap['is_empty'].get((m['type'], m['num']), True) for m in m_cold) if m_cold else True
            is_empty_h = all(ap['is_empty'].get((m['type'], m['num']), True) for m in m_hot) if m_hot else True

            striked_c = ap['striked'].get('cold', False) if m_cold else False
            striked_h = ap['striked'].get('hot', False) if m_hot else False

            if is_empty_c and is_empty_h and not (striked_c and striked_h):
                empty_apts.append(n)

        self.log(f"Найдено пустых квартир: {len(empty_apts)}", "INFO")
        random.shuffle(empty_apts)

        norm_assigned_apts = []

        # --- ФАЗА 1A: Сплошное базовое покрытие (1 жилец) на первый счетчик ---
        self.log("Фаза 1A: Сплошное базовое покрытие (1 жилец)...", "INFO")
        for n in empty_apts:
            ap = all_rows[n]
            striked_c = ap['striked'].get('cold', False) if m_cold else True
            striked_h = ap['striked'].get('hot', False) if m_hot else True

            if striked_c and striked_h:
                continue

            need_c = not striked_c and m_cold
            need_h = not striked_h and m_hot

            can_apply_c = not need_c or (tgt_rem_cold - NORM_COLD >= -0.001)
            can_apply_h = not need_h or (tgt_rem_hot - NORM_HOT >= -0.001)

            if (need_c and not can_apply_c) or (need_h and not can_apply_h):
                continue

            applied_any = False
            if need_c and can_apply_c and f_key_cold:
                ap['consum'][f_key_cold] = round(ap['consum'].get(f_key_cold, 0.0) + NORM_COLD, 3)
                tgt_rem_cold = round(tgt_rem_cold - NORM_COLD, 3)
                applied_any = True

            if need_h and can_apply_h and f_key_hot:
                ap['consum'][f_key_hot] = round(ap['consum'].get(f_key_hot, 0.0) + NORM_HOT, 3)
                tgt_rem_hot = round(tgt_rem_hot - NORM_HOT, 3)
                applied_any = True

            if applied_any:
                ap['is_normative_stage1'] = True
                norm_assigned_apts.append(n)

        self.log(f"Фаза 1A завершена. Базовый норматив (1 жилец) начислен на {len(norm_assigned_apts)} квартир.", "INFO")

        # --- ФАЗА 1B: Последовательный прирост проживающих (+1 жилец) ---
        self.log("Фаза 1B: Последовательный прирост проживающих (+1 жилец)...", "INFO")
        if norm_assigned_apts:
            active_candidates = list(norm_assigned_apts)
            random.shuffle(active_candidates)

            while active_candidates:
                candidate_found = False
                for n in list(active_candidates):
                    ap = all_rows[n]
                    striked_c = ap['striked'].get('cold', False) if m_cold else True
                    striked_h = ap['striked'].get('hot', False) if m_hot else True

                    need_c = not striked_c and m_cold
                    need_h = not striked_h and m_hot

                    can_add_c = not need_c or (tgt_rem_cold - NORM_COLD >= -0.001)
                    can_add_h = not need_h or (tgt_rem_hot - NORM_HOT >= -0.001)

                    if need_c and need_h:
                        if can_add_c and can_add_h:
                            ap['consum'][f_key_cold] = round(ap['consum'].get(f_key_cold, 0.0) + NORM_COLD, 3)
                            ap['consum'][f_key_hot] = round(ap['consum'].get(f_key_hot, 0.0) + NORM_HOT, 3)
                            tgt_rem_cold = round(tgt_rem_cold - NORM_COLD, 3)
                            tgt_rem_hot = round(tgt_rem_hot - NORM_HOT, 3)
                            candidate_found = True
                            break
                        else:
                            active_candidates.remove(n)
                    elif need_c and can_add_c:
                        ap['consum'][f_key_cold] = round(ap['consum'].get(f_key_cold, 0.0) + NORM_COLD, 3)
                        tgt_rem_cold = round(tgt_rem_cold - NORM_COLD, 3)
                        candidate_found = True
                        break
                    elif need_h and can_add_h:
                        ap['consum'][f_key_hot] = round(ap['consum'].get(f_key_hot, 0.0) + NORM_HOT, 3)
                        tgt_rem_hot = round(tgt_rem_hot - NORM_HOT, 3)
                        candidate_found = True
                        break
                    else:
                        active_candidates.remove(n)

                if not candidate_found:
                    break

        self.log("Этап 1 завершён. Нормативы запечатаны (is_normative_stage1 = True) по Закону 2.", "INFO")

        # ==============================================================================
        # ЭТАП 2 И 3: РУЧНАЯ КОРРЕКЦИЯ И ИТЕРАТИВНЫЙ ЦИКЛ ОПРЕДЕЛЕНИЯ ПОРОГА
        # ==============================================================================
        stage1_backup = copy.deepcopy(all_rows)

        # Обработка пользовательского подтверждения ручной коррекции (единократно)
        manual_corr_confirmed = False
        if add_value != 0:
            manual_corr_confirmed = self.request_confirmation(
                f"Добавить {add_value:+.3f} м3 к ХВС?" if add_value > 0 else f"Убавить {abs(add_value):.3f} м3 из ХВС?"
            )
            if manual_corr_confirmed:
                expected_cold = round(expected_cold + add_value, 3)
            else:
                self.log("Операция ручной корректировки отменена пользователем.", "INFO")
                add_value = 0.0

        # Адаптивные шаги ослабления threshold: 0.0 -> 1.0 -> 2.0 ... до 10.0
        thresholds = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        best_rows = None
        best_error = float('inf')
        successful_attempt = False

        self.log("Запуск итеративного модуля подбора распределения...", "INFO")

        for attempt, threshold in enumerate(thresholds):
            if attempt > 0:
                self.log(
                    f"[Итерация {attempt + 1}/{len(thresholds)}] Режим подбора: "
                    f"ослабление порога ХВС >= ГВС - {threshold:.1f} м3...",
                    "WARNING"
                )

            iter_rows = copy.deepcopy(stage1_backup)

            # Выполнение ручной коррекции для текущей итерации
            if add_value != 0 and manual_corr_confirmed:
                self._apply_manual_correction(iter_rows, add_value, m_cold, NORM_COLD, threshold=threshold)

            n_apts = sum(1 for ap in iter_rows.values() if 'квартира' in ap['norm_name'])

            # 2.1. ГВС Распределение (Этап 2)
            curr_h_sum = round(sum(ap['consum'].get((m['type'], m['num']), 0.0) for ap in iter_rows.values() for m in m_hot), 3)
            d_hot = round(expected_hot - curr_h_sum, 3)

            if abs(d_hot) > 0.001 and m_hot:
                avg_shift_h = abs(d_hot) / max(1, n_apts)
                is_emerg_h = (avg_shift_h > 2.0) and (d_hot > 0)

                if is_emerg_h and attempt == 0:
                    self.log(
                        f"[ALERT] Активирован Экстренный режим ГВС! Высокая плотность распределения (+{avg_shift_h:.2f} м3/кв)",
                        "WARNING"
                    )

                elig_h = []
                for n, ap in iter_rows.items():
                    if 'квартира' not in ap['norm_name'] or ap['striked'].get('hot', False) or ap.get('is_normative_stage1', False):
                        continue
                    for m in m_hot:
                        key = (m['type'], m['num'])
                        val = ap['consum'].get(key, 0.0)
                        if is_emerg_h or val >= 0.2 or (ap['orig_fact'].get('hot', False) and val >= 0.2):
                            if m['num'] == 1 and NORM_HOT > 0:
                                ratio = val / NORM_HOT
                                if abs(ratio - round(ratio)) < 0.001 and round(ratio) > 0:
                                    continue
                            elig_h.append((n, key))

                if elig_h:
                    self._distribute_gvs_delta(iter_rows, elig_h, d_hot, m_cold, m_hot, is_emerg_h, threshold=threshold)

            # 2.2. ХВС Распределение (Этап 2)
            curr_c_sum = round(sum(ap['consum'].get((m['type'], m['num']), 0.0) for ap in iter_rows.values() for m in m_cold), 3)
            d_cold = round(expected_cold - curr_c_sum, 3)

            if abs(d_cold) > 0.001 and m_cold:
                elig_c = []
                for n, ap in iter_rows.items():
                    if 'квартира' not in ap['norm_name'] or ap['striked'].get('cold', False) or ap.get('is_normative_stage1', False):
                        continue
                    for m in m_cold:
                        key = (m['type'], m['num'])
                        val = ap['consum'].get(key, 0.0)
                        if (d_cold > 0 and (val >= 0.2 or ap['orig_fact'].get('cold', False))) or (d_cold < 0 and val >= 0.2):
                            if m['num'] == 1 and NORM_COLD > 0:
                                ratio = val / NORM_COLD
                                if abs(ratio - round(ratio)) < 0.001 and round(ratio) > 0:
                                    continue
                            elig_c.append((n, key))

                if elig_c:
                    self._distribute_hvs_delta(iter_rows, elig_c, d_cold, m_cold, m_hot, threshold=threshold)

            # --- ЭТАП 3: Сведение точности (_force_exact_sum) ---
            c_ok = self._force_exact_sum(iter_rows, m_cold, expected_cold, 'cold', NORM_COLD, m_hot, threshold=threshold)
            h_ok = self._force_exact_sum(iter_rows, m_hot, expected_hot, 'hot', NORM_HOT, m_cold, threshold=threshold)

            fin_c_sum = round(sum(ap['consum'].get((m['type'], m['num']), 0.0) for ap in iter_rows.values() for m in m_cold), 3)
            fin_h_sum = round(sum(ap['consum'].get((m['type'], m['num']), 0.0) for ap in iter_rows.values() for m in m_hot), 3)

            err_c = abs(fin_c_sum - expected_cold)
            err_h = abs(fin_h_sum - expected_hot)
            total_err = err_c + err_h

            if total_err < best_error:
                best_error = total_err
                best_rows = iter_rows

            if (c_ok or err_c < 0.0005) and (h_ok or err_h < 0.0005):
                self.log(f"[УСПЕХ] Найдено сбалансированное распределение (порог ослабления = {threshold:.1f} м3)", "SUCCESS")
                successful_attempt = True
                all_rows.clear()
                all_rows.update(iter_rows)
                break

        if not successful_attempt and best_rows:
            self.log(
                f"[ВНИМАНИЕ] Применена оптимальная конфигурация расчёта (минимальная погрешность: {best_error:.3f} м3).",
                "WARNING"
            )
            all_rows.clear()
            all_rows.update(best_rows)

        # Финальная проверка сведения целевых объёмов
        final_cold_sum = round(sum(ap['consum'].get((m['type'], m['num']), 0.0) for ap in all_rows.values() for m in m_cold), 3)
        final_hot_sum = round(sum(ap['consum'].get((m['type'], m['num']), 0.0) for ap in all_rows.values() for m in m_hot), 3)

        if target_cold_val > 0.001:
            if abs(final_cold_sum - expected_cold) < 0.0005:
                self.log(f"Проверка баланса ХВС прошла успешно: Итог ({final_cold_sum:.3f} м3) = Цель ({expected_cold:.3f} м3)", "SUCCESS")
            else:
                self.log(f"Внимание! Баланс ХВС: Итог ({final_cold_sum:.3f} м3) != Цель ({expected_cold:.3f} м3)", "ERROR")

        if target_hot_val > 0.001:
            if abs(final_hot_sum - expected_hot) < 0.0005:
                self.log(f"Проверка баланса ГВС прошла успешно: Итог ({final_hot_sum:.3f} м3) = Цель ({expected_hot:.3f} м3)", "SUCCESS")
            else:
                self.log(f"Внимание! Баланс ГВС: Итог ({final_hot_sum:.3f} м3) != Цель ({expected_hot:.3f} м3)", "ERROR")

        self.log("Расчёт завершён.", "SUCCESS")

    # ==============================================================================
    # ДЕТАЛИЗИРОВАННЫЕ МЕТОДЫ РАСПРЕДЕЛЕНИЯ ДЕЛЬТ
    # ==============================================================================

    def _distribute_gvs_delta(self, r_dict, elig_pairs, delta, m_cold, m_hot, emergency=False, threshold=0.0):
        """
        Распределение ГВС по Законам 1 и 3 с использованием порций +3.0, +2.0, +1.0, +0.5, +0.3, +0.2 м3.
        Приоритет начисления дробных частей — на счетчики с дробными прошлыми показаниями.
        Запрещена порция 0.1 м3 на неактивные квартиры. Проверка соотношения Cons_HVS >= Cons_GVS - threshold.
        """
        rem = delta
        if abs(rem) <= 0.0001:
            return

        active_pairs = [p for p in elig_pairs if r_dict[p[0]]['consum'].get(p[1], 0.0) >= 0.2 or emergency]
        if not active_pairs:
            return

        random.shuffle(active_pairs)

        int_delta = int(math.floor(rem)) if rem > 0 else int(math.ceil(rem))
        frac_delta = round(rem - int_delta, 3)

        # 1. Целая часть и допустимые крупные порции (+3.0, +2.0, +1.0, +0.5, +0.3, +0.2)
        if rem > 0:
            rem_val = rem
            portions = [3.0, 2.0, 1.0, 0.5, 0.3, 0.2]
            idx = 0
            while rem_val >= 0.2 and active_pairs:
                n, key = active_pairs[idx % len(active_pairs)]
                cur_val = r_dict[n]['consum'].get(key, 0.0)

                avail_p = [p for p in portions if p <= rem_val + 1e-5 and self._can_add_gvs(r_dict, n, m_cold, m_hot, p, threshold)]
                if avail_p:
                    chunk = random.choice(avail_p)
                    r_dict[n]['consum'][key] = round(cur_val + chunk, 3)
                    rem_val = round(rem_val - chunk, 3)
                    idx += 1
                else:
                    active_pairs.pop(idx % len(active_pairs))
        else:
            if abs(int_delta) >= 1:
                rem_int = abs(int_delta)
                idx = 0
                while rem_int >= 1 and active_pairs:
                    curr_idx = idx % len(active_pairs)
                    n, key = active_pairs[curr_idx]
                    cur_val = r_dict[n]['consum'].get(key, 0.0)

                    if cur_val - 1.0 >= 0.2:
                        r_dict[n]['consum'][key] = round(cur_val - 1.0, 3)
                        rem_int -= 1
                        idx += 1
                    else:
                        active_pairs.pop(curr_idx)

            if abs(frac_delta) > 0.0001:
                frac_pairs = [p for p in active_pairs if self._is_prev_fractional_meter(r_dict[p[0]], p[1]) or self._is_fractional_meter(r_dict[p[0]], p[1])]
                target_p = frac_pairs[0] if frac_pairs else (active_pairs[0] if active_pairs else None)
                if target_p:
                    n, key = target_p
                    cur_val = r_dict[n]['consum'].get(key, 0.0)
                    if cur_val + frac_delta >= 0.2:
                        r_dict[n]['consum'][key] = round(cur_val + frac_delta, 3)

    def _distribute_hvs_delta(self, r_dict, elig_pairs, delta, m_cold, m_hot, threshold=0.0):
        """Распределение ХВС строго по 3 Законам Человеческого Ввода."""
        if abs(delta) <= 0.0001:
            return

        if delta > 0:
            rem = delta
            int_delta = int(math.floor(rem))
            frac_delta = round(rem - int_delta, 3)

            int_pairs = [p for p in elig_pairs if self._is_integer_meter(r_dict[p[0]], p[1])]
            if not int_pairs:
                int_pairs = list(elig_pairs)
            random.shuffle(int_pairs)

            if int_delta >= 1:
                rem_int = int_delta
                portions = [3.0, 2.0, 1.0]
                idx = 0
                while rem_int >= 1 and int_pairs:
                    n, key = int_pairs[idx % len(int_pairs)]
                    avail_p = [p for p in portions if p <= rem_int]
                    chunk = random.choice(avail_p) if avail_p else 1.0

                    r_dict[n]['consum'][key] = round(r_dict[n]['consum'].get(key, 0.0) + chunk, 3)
                    rem_int -= int(chunk)
                    idx += 1

            if frac_delta > 0.0001:
                frac_pairs = [p for p in elig_pairs if self._is_prev_fractional_meter(r_dict[p[0]], p[1]) or self._is_fractional_meter(r_dict[p[0]], p[1])]
                if not frac_pairs:
                    frac_pairs = list(elig_pairs)
                random.shuffle(frac_pairs)

                target_n, target_key = frac_pairs[0]
                r_dict[target_n]['consum'][target_key] = round(r_dict[target_n]['consum'].get(target_key, 0.0) + frac_delta, 3)

        else:
            req = abs(delta)

            total_avail_safe = 0.0
            for n, key in elig_pairs:
                cold_tot = sum(r_dict[n]['consum'].get((m['type'], m['num']), 0.0) for m in m_cold)
                hot_tot = sum(r_dict[n]['consum'].get((m['type'], m['num']), 0.0) for m in m_hot)
                cur_val = r_dict[n]['consum'].get(key, 0.0)
                safe_sub = max(0.0, min(cur_val - 0.2, cold_tot + threshold - hot_tot))
                total_avail_safe += safe_sub

            if total_avail_safe < req - 0.001 and threshold == 0.0:
                self.log(
                    "[EMERGENCY MINUS] Достигнут критический предел ХВС >= ГВС! Переход на глубокую балансировку.",
                    "WARNING"
                )

            int_req = int(math.floor(req))
            frac_req = round(req - int_req, 3)

            # При списании в минус приоритет отдаем 2-му и последующим счетчикам (m['num'] > 1)
            active_pairs = sorted(elig_pairs, key=lambda p: p[1][1] if isinstance(p[1], tuple) else 1, reverse=True)

            if int_req >= 1:
                rem_int = int_req
                portions = [3.0, 2.0, 1.0]
                idx = 0
                while rem_int >= 1 and active_pairs:
                    curr_idx = idx % len(active_pairs)
                    n, key = active_pairs[curr_idx]
                    cur_val = r_dict[n]['consum'].get(key, 0.0)

                    if total_avail_safe < req - 0.001:
                        max_sub = max(0.0, cur_val - 0.2)
                    else:
                        cold_tot = sum(r_dict[n]['consum'].get((m['type'], m['num']), 0.0) for m in m_cold)
                        hot_tot = sum(r_dict[n]['consum'].get((m['type'], m['num']), 0.0) for m in m_hot)
                        max_sub = max(0.0, min(cur_val - 0.2, cold_tot + threshold - hot_tot))

                    avail_p = [p for p in portions if p <= rem_int and p <= max_sub]
                    if avail_p:
                        sub = random.choice(avail_p)
                        r_dict[n]['consum'][key] = round(cur_val - sub, 3)
                        rem_int -= int(sub)
                        idx += 1
                    else:
                        active_pairs.pop(curr_idx)

            if frac_req > 0.0001 and active_pairs:
                frac_pairs = [p for p in active_pairs if self._is_prev_fractional_meter(r_dict[p[0]], p[1]) or self._is_fractional_meter(r_dict[p[0]], p[1])]
                target_list = frac_pairs if frac_pairs else active_pairs
                for n, key in target_list:
                    cur_val = r_dict[n]['consum'].get(key, 0.0)
                    if self._can_sub_hvs(r_dict, n, m_cold, m_hot, frac_req, threshold) and cur_val - frac_req >= 0.2:
                        r_dict[n]['consum'][key] = round(cur_val - frac_req, 3)
                        break

    # ==============================================================================
    # ФИНАЛЬНОЕ ПРИНУДИТЕЛЬНОЕ СВЕДЕНИЕ (100% БАЛАНС С КАСКАДНЫМ ВЫБОРОМ)
    # ==============================================================================

    def _force_exact_sum(self, r_dict, m_list, expected_target, f_key_type, norm_val, other_m_list=None, threshold=0.0):
        """
        Метод гарантирует 100% точность сведения целевой суммы до 0.000 м3 (допуск < 0.0005).
        Каскадный выбор кандидатов:
        - Нормативы (4.04, 8.08, 2.65, 5.30) полностью ИСКЛЮЧЕНЫ по Закону 2 (is_normative_stage1 = True).
        - Приоритет 1: Дробные счётчики с прошлыми дробными показаниями или 3 знаками ('по среднему') с val >= 0.2 м3.
        - Приоритет 2 (Fallback): Любые дробные счётчики с val >= 0.2 м3.
        """
        if not m_list or expected_target <= 0.0001:
            return True

        m_cold = m_list if f_key_type == 'cold' else (other_m_list or [])
        m_hot = m_list if f_key_type == 'hot' else (other_m_list or [])

        curr_sum = round(sum(ap['consum'].get((m['type'], m['num']), 0.0) for ap in r_dict.values() for m in m_list), 3)
        diff = round(expected_target - curr_sum, 3)

        if abs(diff) < 0.0005:
            return True

        p1_pairs = []
        p2_pairs = []

        for n, ap in r_dict.items():
            if 'квартира' not in ap['norm_name']:
                continue
            if ap['striked'].get(f_key_type, False):
                continue
            if ap.get('is_normative_stage1', False):  # Закон 2: Нормативы 100% запечатаны!
                continue

            for m in m_list:
                key = (m['type'], m['num'])
                val = ap['consum'].get(key, 0.0)

                if val < 0.2:  # Предохранитель 1: Малые значения и нули пропускаются
                    continue

                if self._is_integer_meter(ap, key):  # Закон 1: Целые запрещены для копеек
                    continue

                if m['num'] == 1 and norm_val > 0:
                    ratio = val / norm_val
                    if abs(ratio - round(ratio)) < 0.001 and round(ratio) > 0:
                        continue

                pair = (n, key)
                p2_pairs.append(pair)
                if self._is_3dec_meter(ap, key) or self._is_prev_fractional_meter(ap, key):
                    p1_pairs.append(pair)

        target_pairs = p1_pairs if p1_pairs else p2_pairs

        if not target_pairs:
            return False

        step = 0.001 if diff > 0 else -0.001
        steps_needed = int(round(abs(diff) / 0.001))

        active_pairs = list(target_pairs)
        random.shuffle(active_pairs)
        idx = 0

        for _ in range(steps_needed):
            if not active_pairs:
                break
            curr_idx = idx % len(active_pairs)
            n, key = active_pairs[curr_idx]
            cur_val = r_dict[n]['consum'][key]

            new_val = round(cur_val + step, 3)

            # Предохранитель 2: Запрет комбинаций 0.101 м3 или превращения в val < 0.2 м3
            if abs(new_val - 0.101) < 1e-4 or new_val < 0.2:
                active_pairs.pop(curr_idx)
                continue

            if f_key_type == 'hot' and step > 0:
                if not self._can_add_gvs(r_dict, n, m_cold, m_hot, step, threshold):
                    active_pairs.pop(curr_idx)
                    continue

            if f_key_type == 'cold' and step < 0:
                if not self._can_sub_hvs(r_dict, n, m_cold, m_hot, abs(step), threshold):
                    active_pairs.pop(curr_idx)
                    continue

            r_dict[n]['consum'][key] = new_val
            idx += 1

        final_sum = round(sum(ap['consum'].get((m['type'], m['num']), 0.0) for ap in r_dict.values() for m in m_list), 3)
        return abs(final_sum - expected_target) < 0.0005