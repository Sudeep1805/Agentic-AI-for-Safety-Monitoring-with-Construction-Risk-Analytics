import { test, expect } from '@playwright/test'
import path from 'node:path'

test('browser upload persists in MySQL, reloads history, and works on mobile', async ({ page, request }) => {
  const browserErrors = []
  page.on('pageerror', (error) => browserErrors.push(error.message))
  await page.goto('/')
  await expect(page.getByText('Database connected')).toBeVisible()
  await page.getByLabel('Choose site photograph').setInputFiles(path.resolve('../.local/test-site.png'))
  await expect(page.getByAltText('Selected construction site photograph')).toBeVisible()
  await page.getByLabel('Site context (optional)').fill('Verification fixture only; not a real site assessment.')
  const savedResponse = page.waitForResponse((response) => response.url().endsWith('/api/uploads') && response.request().method() === 'POST')
  await page.getByRole('button', { name: 'Save observation' }).click()
  const response = await savedResponse
  expect(response.status()).toBe(201)
  const record = await response.json()
  expect(record.analysis_status).toBe('unavailable')
  expect(record.risk_score).toBeNull()
  await expect(page.getByText('Upload saved successfully.')).toBeVisible()
  await expect(page.getByText('Saved · Not assessed')).toBeVisible()
  const image = await request.get(`${process.env.FOUNDATION_API_URL}${record.image_url}`)
  expect(image.status()).toBe(200)
  expect(image.headers()['content-type']).toBe('image/png')
  await page.reload()
  await expect(page.getByText('Saved · Not assessed')).toBeVisible()
  await page.getByRole('button', { name: /test-site.png/ }).click()
  await expect(page.getByText('Verification fixture only; not a real site assessment.')).toBeVisible()
  await page.screenshot({ path: '../.local/desktop-upload.png', fullPage: true })
  await page.setViewportSize({ width: 390, height: 844 })
  await expect(page.getByRole('heading', { name: 'Upload a site image' })).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
  await page.screenshot({ path: '../.local/mobile-upload.png', fullPage: true })
  expect(browserErrors).toEqual([])
})

test('live API rejects corrupt image content without success', async ({ request }) => {
  const response = await request.post(`${process.env.FOUNDATION_API_URL}/api/uploads`, {
    multipart: { file: { name: 'fake.png', mimeType: 'image/png', buffer: Buffer.from('not an image') } },
  })
  expect(response.status()).toBe(422)
  expect(await response.json()).toEqual({ detail: 'The file is not a complete, readable image.' })
})
