import { mkdir, copyFile } from 'node:fs/promises'
const destination = new URL('../public/data/', import.meta.url)
await mkdir(destination, { recursive: true })
for (const file of ['northstar.json', 'real-extracts.json']) {
  await copyFile(new URL(`../data/${file}`, import.meta.url), new URL(file, destination))
}
