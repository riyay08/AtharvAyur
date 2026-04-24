import { useCallback, useEffect, useMemo, useState } from "react";

import {
  DEFAULT_FORM,
  formFromRecord,
  localYmd,
  normalizeYmd,
} from "../models/checkinModel.js";
import {
  getCheckInWeek as getCheckInWeekApi,
  postCheckIn as postCheckInApi,
} from "../services/checkinService.js";

/**
 * ViewModel for the DailyCheckIn feature.
 *
 * @param {{
 *   userId: string | null,
 *   getCheckInWeek?: typeof getCheckInWeekApi,
 *   postCheckIn?: typeof postCheckInApi,
 * }} params
 */
export function useDailyCheckInViewModel({
  userId,
  getCheckInWeek = getCheckInWeekApi,
  postCheckIn = postCheckInApi,
}) {
  const [weekData, setWeekData] = useState(/** @type {any} */ (null));
  const [weekLoading, setWeekLoading] = useState(false);
  const [weekError, setWeekError] = useState(/** @type {string | null} */ (null));

  const todayStr = useMemo(() => localYmd(), []);
  const [selectedDate, setSelectedDate] = useState(todayStr);
  const [isFormExpanded, setIsFormExpanded] = useState(true);
  const [expandInitialized, setExpandInitialized] = useState(false);

  const [form, setForm] = useState(DEFAULT_FORM);
  const [status, setStatus] = useState(/** @type {'idle'|'loading'|'error'} */ ("idle"));
  const [message, setMessage] = useState(/** @type {string | null} */ (null));

  const applyRecord = useCallback((rec) => setForm(formFromRecord(rec)), []);

  const loadWeek = useCallback(async () => {
    if (!userId) {
      setWeekData(null);
      return;
    }
    setWeekLoading(true);
    setWeekError(null);
    try {
      const data = await getCheckInWeek(localYmd());
      setWeekData(data);
    } catch (e) {
      setWeekError(e instanceof Error ? e.message : "Could not load check-ins.");
      setWeekData(null);
    } finally {
      setWeekLoading(false);
    }
  }, [userId, getCheckInWeek]);

  useEffect(() => {
    setExpandInitialized(false);
  }, [userId]);

  useEffect(() => {
    loadWeek();
  }, [loadWeek]);

  useEffect(() => {
    if (!weekData?.days || expandInitialized) return;
    const t = localYmd();
    setSelectedDate(t);
    const slot = weekData.days.find((s) => normalizeYmd(s.check_in_date) === t);
    setIsFormExpanded(!slot?.record);
    applyRecord(slot?.record ?? null);
    setExpandInitialized(true);
  }, [weekData, expandInitialized, applyRecord]);

  useEffect(() => {
    if (!weekData?.days) return;
    const slot = weekData.days.find((s) => normalizeYmd(s.check_in_date) === selectedDate);
    applyRecord(slot?.record ?? null);
  }, [selectedDate, weekData, applyRecord]);

  const selectDay = useCallback((ymd) => {
    setSelectedDate(ymd);
    setIsFormExpanded(true);
    setMessage(null);
  }, []);

  const update = useCallback((patch) => setForm((f) => ({ ...f, ...patch })), []);

  const setWater = useCallback((n) => update({ water: Math.max(0, n) }), [update]);

  const submit = useCallback(async () => {
    if (!userId) return;
    setStatus("loading");
    setMessage(null);
    try {
      const saved = await postCheckIn({
        check_in_date: selectedDate,
        sleep_quality: form.sleepQuality,
        digestion: form.digestion,
        energy_state: form.energyState,
        movement: form.movement,
        water_glasses: form.water,
      });
      const refreshed = await getCheckInWeek(localYmd());
      setWeekData(refreshed);
      const ymd = normalizeYmd(saved.check_in_date) || selectedDate;
      setSelectedDate(ymd);
      applyRecord(saved);
      setIsFormExpanded(false);
      setStatus("idle");
      setMessage("Saved.");
      setTimeout(() => setMessage(null), 2200);
    } catch (e) {
      setStatus("error");
      setMessage(e instanceof Error ? e.message : "Could not save check-in.");
    }
  }, [userId, form, selectedDate, postCheckIn, getCheckInWeek, applyRecord]);

  const stripDays = weekData?.days ?? [];

  return {
    // data
    weekData,
    weekLoading,
    weekError,
    stripDays,
    todayStr,
    selectedDate,
    isFormExpanded,
    // form
    sleepQuality: form.sleepQuality,
    digestion: form.digestion,
    energyState: form.energyState,
    movement: form.movement,
    water: form.water,
    // status
    status,
    message,
    // actions
    setIsFormExpanded,
    selectDay,
    setSleepQuality: (v) => update({ sleepQuality: v }),
    setDigestion: (v) => update({ digestion: v }),
    setEnergyState: (v) => update({ energyState: v }),
    setMovement: (v) => update({ movement: v }),
    setWater,
    submit,
  };
}
