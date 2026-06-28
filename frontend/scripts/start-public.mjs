import { spawn } from 'node:child_process'
import { existsSync } from 'node:fs'
import path from 'node:path'
import process from 'node:process'

const FRONTEND_PORT = 5173
const isWindows = process.platform === 'win32'

const cpolarCommand =
  process.env.CPOLAR_EXE?.trim() ||
  (isWindows ? 'cpolar.exe' : 'cpolar')

let cpolarProcess = null
let viteProcess = null
let publicUrl = ''
let publicHost = ''
let cpolarOutput = ''
let viteOutput = ''
let viteStarted = false
let printed = false
let shuttingDown = false

function stopProcessTree(child) {
  if (!child || child.exitCode !== null || child.signalCode !== null) {
    return
  }

  if (isWindows) {
    const killer = spawn(
      'taskkill.exe',
      ['/PID', String(child.pid), '/T', '/F'],
      {
        stdio: 'ignore',
        windowsHide: true
      }
    )

    killer.unref()
  } else {
    child.kill('SIGTERM')
  }
}

function shutdown(exitCode = 0) {
  if (shuttingDown) {
    return
  }

  shuttingDown = true

  stopProcessTree(viteProcess)
  stopProcessTree(cpolarProcess)

  setTimeout(() => {
    process.exit(exitCode)
  }, 400)
}

function printAddresses() {
  if (printed) {
    return
  }

  printed = true

  console.log(`\n本地地址：http://localhost:${FRONTEND_PORT}/`)
  console.log(`公网地址：${publicUrl}\n`)
}

function startVite() {
  if (viteStarted) {
    return
  }

  viteStarted = true

  const viteCliPath = path.resolve(
    process.cwd(),
    'node_modules',
    'vite',
    'bin',
    'vite.js'
  )

  if (!existsSync(viteCliPath)) {
    console.error(
      '启动失败：找不到 Vite，请先在 frontend 目录运行 npm install。'
    )
    shutdown(1)
    return
  }

  viteProcess = spawn(
    process.execPath,
    [viteCliPath],
    {
      cwd: process.cwd(),

      env: {
        ...process.env,
        __VITE_ADDITIONAL_SERVER_ALLOWED_HOSTS: publicHost
      },

      windowsHide: true,

      stdio: [
        'ignore',
        'pipe',
        'pipe'
      ]
    }
  )

  viteProcess.stdout.on('data', chunk => {
    viteOutput += chunk.toString()

    if (/ready in/i.test(viteOutput)) {
      printAddresses()
    }
  })

  viteProcess.stderr.on('data', chunk => {
    const text = chunk.toString()

    if (/error|failed|exception|eaddrinuse/i.test(text)) {
      process.stderr.write(text)
    }
  })

  viteProcess.on('error', error => {
    console.error(`启动 Vite 失败：${error.message}`)
    shutdown(1)
  })

  viteProcess.on('exit', code => {
    if (!shuttingDown) {
      if (code !== 0) {
        console.error(`Vite 已退出，退出码：${code}`)
      }

      shutdown(code ?? 0)
    }
  })
}

function inspectCpolarOutput(chunk) {
  cpolarOutput += chunk.toString()

  if (publicUrl) {
    return
  }

  const match = cpolarOutput.match(
    /https:\/\/([A-Za-z0-9.-]+\.cpolar\.(?:top|cn|com|io))/i
  )

  if (!match) {
    return
  }

  publicUrl = match[0]
  publicHost = match[1]

  startVite()
}

cpolarProcess = spawn(
  cpolarCommand,
  [
    'http',
    '-log=stdout',
    String(FRONTEND_PORT)
  ],
  {
    cwd: process.cwd(),
    env: process.env,
    windowsHide: true,

    stdio: [
      'ignore',
      'pipe',
      'pipe'
    ]
  }
)

cpolarProcess.stdout.on('data', inspectCpolarOutput)
cpolarProcess.stderr.on('data', inspectCpolarOutput)

cpolarProcess.on('error', error => {
  console.error(`启动 cpolar 失败：${error.message}`)
  console.error('请检查 JetBrains 中的 CPOLAR_EXE 环境变量。')
  shutdown(1)
})

cpolarProcess.on('exit', code => {
  if (!shuttingDown) {
    console.error(`cpolar 已退出，退出码：${code ?? 0}`)
    shutdown(code || 1)
  }
})

const startupTimeout = setTimeout(() => {
  if (!publicUrl && !shuttingDown) {
    console.error(
      '启动失败：45 秒内没有获取到 cpolar 公网地址。'
    )
    shutdown(1)
  }
}, 45_000)

startupTimeout.unref()

process.on('SIGINT', () => {
  shutdown(0)
})

process.on('SIGTERM', () => {
  shutdown(0)
})