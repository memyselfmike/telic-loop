import { NextRequest, NextResponse } from 'next/server'

/**
 * Next.js middleware to handle CORS preflight requests
 * This runs before Payload CMS routes and adds proper CORS headers
 */
export function middleware(request: NextRequest) {
  // Handle OPTIONS preflight requests
  if (request.method === 'OPTIONS') {
    return new NextResponse(null, {
      status: 200,
      headers: {
        'Access-Control-Allow-Origin': 'http://localhost:4321',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Max-Age': '86400',
      },
    })
  }

  // For all other requests, add CORS headers to the response
  const response = NextResponse.next()
  response.headers.set('Access-Control-Allow-Origin', 'http://localhost:4321')
  response.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
  response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization')

  return response
}

// Apply middleware to API routes only
export const config = {
  matcher: '/api/:path*',
}
