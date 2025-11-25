import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { declinePublicationSchema } from "@/lib/schemas"
import type { z } from "zod"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Textarea } from "@/components/ui/textarea"
import { useDeclinePublication } from "@/hooks/use-publications"
import type { PublicationRead } from "@/types/api"

type DeclinePublicationFormValues = z.infer<typeof declinePublicationSchema>

interface DeclinePublicationDialogProps {
  publication: PublicationRead
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function DeclinePublicationDialog({
  publication,
  open,
  onOpenChange,
}: DeclinePublicationDialogProps) {
  const declinePublication = useDeclinePublication()

  const form = useForm<DeclinePublicationFormValues>({
    resolver: zodResolver(declinePublicationSchema),
    defaultValues: {
      reason: "",
    },
  })

  const onSubmit = async (data: DeclinePublicationFormValues) => {
    await declinePublication.mutateAsync({
      pubId: publication.id,
      reason: data.reason,
    })
    onOpenChange(false)
    form.reset()
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Отклонить публикацию</DialogTitle>
          <DialogDescription>
            Укажите причину отклонения публикации "{publication.title}".
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="reason"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Причина отклонения</FormLabel>
                  <FormControl>
                    <Textarea {...field} rows={4} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
              >
                Отмена
              </Button>
              <Button
                type="submit"
                variant="destructive"
                disabled={declinePublication.isPending}
              >
                Отклонить
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

