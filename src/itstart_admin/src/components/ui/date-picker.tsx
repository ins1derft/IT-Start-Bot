import * as React from "react"
import { format } from "date-fns"
import { ru } from "date-fns/locale"
import { FiCalendar } from "react-icons/fi"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"

interface DatePickerProps {
  value?: Date | null
  onChange: (date: Date | null) => void
  placeholder?: string
  disabled?: boolean
  className?: string
}

export function DatePicker({
  value,
  onChange,
  placeholder = "Выберите дату",
  disabled,
  className,
}: DatePickerProps) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant={"outline"}
          className={cn(
            "w-full justify-start text-left font-normal",
            !value && "text-muted-foreground",
            className
          )}
          disabled={disabled}
        >
          <FiCalendar className="mr-2 h-4 w-4" />
          {value ? (
            format(value, "PPP", { locale: ru })
          ) : (
            <span>{placeholder}</span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="start">
        <Calendar
          mode="single"
          selected={value || undefined}
          onSelect={(date) => onChange(date || null)}
          initialFocus
          locale={ru}
        />
      </PopoverContent>
    </Popover>
  )
}

interface DateTimePickerProps {
  value?: Date | null
  onChange: (date: Date | null) => void
  placeholder?: string
  disabled?: boolean
  className?: string
}

export function DateTimePicker({
  value,
  onChange,
  placeholder = "Выберите дату и время",
  disabled,
  className,
}: DateTimePickerProps) {
  const [date, setDate] = React.useState<Date | null>(value || null)
  const [time, setTime] = React.useState<string>(
    value ? format(value, "HH:mm") : ""
  )

  React.useEffect(() => {
    if (value) {
      setDate(value)
      setTime(format(value, "HH:mm"))
    }
  }, [value])

  const handleDateChange = (newDate: Date | null) => {
    setDate(newDate)
    if (newDate && time) {
      const [hours, minutes] = time.split(":")
      const dateTime = new Date(newDate)
      dateTime.setHours(parseInt(hours, 10))
      dateTime.setMinutes(parseInt(minutes, 10))
      onChange(dateTime)
    } else {
      onChange(newDate)
    }
  }

  const handleTimeChange = (newTime: string) => {
    setTime(newTime)
    if (date && newTime) {
      const [hours, minutes] = newTime.split(":")
      const dateTime = new Date(date)
      dateTime.setHours(parseInt(hours, 10))
      dateTime.setMinutes(parseInt(minutes, 10))
      onChange(dateTime)
    }
  }

  return (
    <div className={cn("flex gap-2", className)}>
      <Popover>
        <PopoverTrigger asChild>
          <Button
            variant={"outline"}
            className={cn(
              "flex-1 justify-start text-left font-normal",
              !date && "text-muted-foreground"
            )}
            disabled={disabled}
          >
            <FiCalendar className="mr-2 h-4 w-4" />
            {date ? (
              format(date, "PPP", { locale: ru })
            ) : (
              <span>Выберите дату</span>
            )}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar
            mode="single"
            selected={date || undefined}
            onSelect={handleDateChange}
            initialFocus
            locale={ru}
          />
        </PopoverContent>
      </Popover>
      <input
        type="time"
        value={time}
        onChange={(e) => handleTimeChange(e.target.value)}
        className="flex h-10 w-32 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
        disabled={disabled}
      />
    </div>
  )
}

