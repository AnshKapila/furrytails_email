export {};

declare global {
  interface Window {
    __kite?: { conversion: (goalType: string) => void };
  }
}
