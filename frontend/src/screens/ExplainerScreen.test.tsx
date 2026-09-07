import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { ExplainerScreen } from './ExplainerScreen'

/** jsdom has no camera, so stand one in for the duration of a test. */
function stubCamera(result: () => Promise<MediaStream>) {
  const getUserMedia = vi.fn(result)
  Object.defineProperty(navigator, 'mediaDevices', {
    value: { getUserMedia },
    configurable: true,
  })
  return getUserMedia
}

afterEach(() => {
  Reflect.deleteProperty(navigator, 'mediaDevices')
})

function clickEnable() {
  fireEvent.click(screen.getByRole('button', { name: /turn on the camera/i }))
}

describe('ExplainerScreen', () => {
  it('says what the camera is for before any permission prompt', () => {
    const getUserMedia = stubCamera(() => Promise.resolve({} as MediaStream))

    render(<ExplainerScreen onGranted={() => {}} />)

    expect(screen.getByText(/video never leaves the phone/i)).toBeInTheDocument()
    expect(getUserMedia).not.toHaveBeenCalled()
  })

  it('asks for the selfie camera at 30 fps and hands the stream on', async () => {
    const stream = {} as MediaStream
    const getUserMedia = stubCamera(() => Promise.resolve(stream))
    const onGranted = vi.fn()

    render(<ExplainerScreen onGranted={onGranted} />)
    clickEnable()

    await waitFor(() => expect(onGranted).toHaveBeenCalledWith(stream))
    expect(getUserMedia).toHaveBeenCalledWith(
      expect.objectContaining({
        video: expect.objectContaining({ facingMode: 'user', frameRate: { ideal: 30 } }),
      }),
    )
  })

  it('explains a denial and leaves the button ready to try again', async () => {
    const denial = new Error('Permission denied')
    denial.name = 'NotAllowedError'
    stubCamera(() => Promise.reject(denial))
    const onGranted = vi.fn()

    render(<ExplainerScreen onGranted={onGranted} />)
    clickEnable()

    expect(await screen.findByRole('alert')).toHaveTextContent(/blocked/i)
    expect(screen.getByRole('button', { name: /turn on the camera/i })).toBeEnabled()
    expect(onGranted).not.toHaveBeenCalled()
  })
})
