import './globals.css';

export const metadata = {
  title: 'Operations Agent',
  description: 'Grounded AWS Bedrock operations assistant'
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
