import { useMutation } from "@tanstack/react-query"
import api from "@/lib/api"
import { useToast } from "@/components/ui/use-toast"

export function useExportPublications() {
  const { toast } = useToast()

  return useMutation({
    mutationFn: async (data: {
      date_from?: string | null
      date_to?: string | null
      fmt?: string
    }) => {
      const searchParams = new URLSearchParams()
      if (data.date_from) {
        searchParams.set("date_from", data.date_from)
      }
      if (data.date_to) {
        searchParams.set("date_to", data.date_to)
      }
      if (data.fmt) {
        searchParams.set("fmt", data.fmt)
      }

      const response = await api.get("admin/export/publications", {
        searchParams: searchParams.toString(),
      })

      // Create blob and download
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `publications_${data.date_from || "all"}_${data.date_to || "all"}.${data.fmt || "csv"}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      return blob
    },
    onSuccess: () => {
      toast({
        title: "Экспорт выполнен",
        description: "Публикации успешно экспортированы",
      })
    },
    onError: (error: any) => {
      toast({
        title: "Ошибка",
        description: error?.message || "Не удалось экспортировать публикации",
        variant: "destructive",
      })
    },
  })
}

