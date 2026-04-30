from supabase import create_client

url = "https://urptyxmtkhdgptqsizvi.supabase.co"
key = "你的 anon key"

supabase = create_client(url, key)

res = supabase.table("expenses").select("*").execute()
print(res.data)