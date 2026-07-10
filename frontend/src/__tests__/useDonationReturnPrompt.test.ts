import { renderHook, act } from '@testing-library/react'
import { useDonationReturnPrompt } from '../hooks/useDonationReturnPrompt'

function fireVisibilityChange(state: DocumentVisibilityState) {
  Object.defineProperty(document, 'visibilityState', { value: state, configurable: true })
  document.dispatchEvent(new Event('visibilitychange'))
}

beforeEach(() => {
  sessionStorage.clear()
  jest.useFakeTimers()
})

afterEach(() => {
  jest.useRealTimers()
})

describe('useDonationReturnPrompt', () => {
  it('does not show a prompt before any donate click is tracked', () => {
    const { result } = renderHook(() => useDonationReturnPrompt())
    act(() => fireVisibilityChange('visible'))
    expect(result.current.promptState).toBeNull()
  })

  it('shows the prompt on return after the minimum away-time has passed', () => {
    const { result } = renderHook(() => useDonationReturnPrompt())
    act(() => result.current.trackDonateClick('123456789', 'Save the World'))
    act(() => jest.advanceTimersByTime(3_500))
    act(() => fireVisibilityChange('visible'))
    expect(result.current.promptState).toEqual({ ein: '123456789', name: 'Save the World' })
  })

  it('does NOT show the prompt on an instant tab switch (popup blocked, etc)', () => {
    const { result } = renderHook(() => useDonationReturnPrompt())
    act(() => result.current.trackDonateClick('123456789', 'Save the World'))
    // no time advance -- immediate return
    act(() => fireVisibilityChange('visible'))
    expect(result.current.promptState).toBeNull()
  })

  it('ignores visibilitychange to hidden (only fires on becoming visible)', () => {
    const { result } = renderHook(() => useDonationReturnPrompt())
    act(() => result.current.trackDonateClick('123456789', 'Save the World'))
    act(() => jest.advanceTimersByTime(3_500))
    act(() => fireVisibilityChange('hidden'))
    expect(result.current.promptState).toBeNull()
  })

  it('dismiss() clears the prompt and prevents it from reappearing on the next visibility event', () => {
    const { result } = renderHook(() => useDonationReturnPrompt())
    act(() => result.current.trackDonateClick('123456789', 'Save the World'))
    act(() => jest.advanceTimersByTime(3_500))
    act(() => fireVisibilityChange('visible'))
    expect(result.current.promptState).not.toBeNull()

    act(() => result.current.dismiss())
    expect(result.current.promptState).toBeNull()

    // a later, unrelated visibility flicker must not resurrect the same prompt
    act(() => fireVisibilityChange('hidden'))
    act(() => fireVisibilityChange('visible'))
    expect(result.current.promptState).toBeNull()
  })

  it('persists the pending click across a fresh hook instance via sessionStorage (survives a reload while away)', () => {
    const first = renderHook(() => useDonationReturnPrompt())
    act(() => first.result.current.trackDonateClick('987654321', 'Local Food Bank'))
    act(() => jest.advanceTimersByTime(3_500))

    // simulate the page reloading while the donor is still away: a brand new
    // hook instance, but sessionStorage should carry the pending click over
    const second = renderHook(() => useDonationReturnPrompt())
    act(() => fireVisibilityChange('visible'))
    expect(second.result.current.promptState).toEqual({ ein: '987654321', name: 'Local Food Bank' })
  })
})
