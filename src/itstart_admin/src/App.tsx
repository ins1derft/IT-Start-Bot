import { RouterProvider } from "react-router-dom"
import { QueryProvider } from "@/providers/QueryProvider"
import { Toaster } from "@/components/ui/toaster"
import { router } from "@/router"

function App() {
  return (
    <QueryProvider>
      <RouterProvider router={router} />
      <Toaster />
    </QueryProvider>
  )
}

export default App
