import React from 'react'
import { RootLayout } from '@payloadcms/next/layouts'
import '@payloadcms/ui/styles.css'
import '@payloadcms/next/css'

import config from '@payload-config'

export default async function Layout({ children }: { children: React.ReactNode }) {
  return (
    <RootLayout config={config}>
      {children}
    </RootLayout>
  )
}
