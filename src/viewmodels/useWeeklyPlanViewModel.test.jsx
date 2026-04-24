import { act, renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { useWeeklyPlanViewModel } from "./useWeeklyPlanViewModel.js";

describe("useWeeklyPlanViewModel", () => {
  it("loads the plan on mount when a user id is present", async () => {
    const plan = { id: "p1", start_date: "2026-04-20", tasks: { days: [] } };
    const getCurrentPlan = vi.fn().mockResolvedValue(plan);
    const generateWeeklyPlan = vi.fn();

    const { result } = renderHook(() =>
      useWeeklyPlanViewModel({ userId: "u-1", getCurrentPlan, generateWeeklyPlan })
    );

    await waitFor(() => {
      expect(result.current.plan).toEqual(plan);
    });
    expect(getCurrentPlan).toHaveBeenCalledTimes(1);
    expect(result.current.showEnvelope).toBe(true);
    expect(result.current.showLegacy).toBe(false);
  });

  it("does not fetch when there is no user id", async () => {
    const getCurrentPlan = vi.fn();
    const generateWeeklyPlan = vi.fn();
    const { result } = renderHook(() =>
      useWeeklyPlanViewModel({ userId: null, getCurrentPlan, generateWeeklyPlan })
    );

    expect(getCurrentPlan).not.toHaveBeenCalled();
    expect(result.current.plan).toBeNull();
  });

  it("surfaces errors on load and on generate", async () => {
    const getCurrentPlan = vi.fn().mockRejectedValue(new Error("boom"));
    const generateWeeklyPlan = vi.fn().mockRejectedValue(new Error("gen failed"));

    const { result } = renderHook(() =>
      useWeeklyPlanViewModel({ userId: "u-1", getCurrentPlan, generateWeeklyPlan })
    );

    await waitFor(() => {
      expect(result.current.error).toBe("boom");
    });

    await act(async () => {
      await result.current.generate();
    });
    expect(result.current.error).toBe("gen failed");
  });

  it("replaces the plan when generate succeeds", async () => {
    const existing = { id: "old", start_date: "2026-04-13", tasks: [] };
    const fresh = { id: "new", start_date: "2026-04-20", tasks: { days: [] } };
    const getCurrentPlan = vi.fn().mockResolvedValue(existing);
    const generateWeeklyPlan = vi.fn().mockResolvedValue(fresh);

    const { result } = renderHook(() =>
      useWeeklyPlanViewModel({ userId: "u-1", getCurrentPlan, generateWeeklyPlan })
    );
    await waitFor(() => expect(result.current.plan).toEqual(existing));

    await act(async () => {
      await result.current.generate();
    });

    expect(result.current.plan).toEqual(fresh);
    expect(result.current.genLoading).toBe(false);
  });
});
