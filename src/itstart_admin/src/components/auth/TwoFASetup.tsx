import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { otpCodeSchema } from "@/lib/schemas"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { QRCodeSVG } from "qrcode.react"
import type { z } from "zod"

type OTPFormValues = z.infer<typeof otpCodeSchema>

interface TwoFASetupProps {
  secret: string
  onConfirm: (code: string) => void
  onCancel: () => void
}

export function TwoFASetup({ secret, onConfirm, onCancel }: TwoFASetupProps) {
  const form = useForm<OTPFormValues>({
    resolver: zodResolver(otpCodeSchema),
    defaultValues: {
      code: "",
    },
  })

  const onSubmit = (data: OTPFormValues) => {
    onConfirm(data.code)
  }

  // Generate provisioning URI (this should match backend format)
  const provisioningUri = `otpauth://totp/ITStart%20Admin?secret=${secret}&issuer=ITStart`

  return (
    <div className="space-y-4">
      <div className="flex justify-center">
        <QRCodeSVG value={provisioningUri} size={200} />
      </div>
      <div className="text-center text-sm text-muted-foreground">
        Секретный ключ: <code className="font-mono">{secret}</code>
      </div>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <FormField
            control={form.control}
            name="code"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Код подтверждения</FormLabel>
                <FormControl>
                  <Input
                    {...field}
                    placeholder="000000"
                    maxLength={6}
                    className="text-center text-2xl tracking-widest"
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <div className="flex gap-2">
            <Button type="submit" className="flex-1">
              Подтвердить
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
              className="flex-1"
            >
              Отмена
            </Button>
          </div>
        </form>
      </Form>
    </div>
  )
}

