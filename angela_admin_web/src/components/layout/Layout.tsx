import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'

export default function Layout() {
  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-950 transition-colors">
      <Sidebar />
      <main className="flex-1 overflow-y-auto dark:text-gray-100">
        <Outlet />
      </main>
    </div>
  )
}
