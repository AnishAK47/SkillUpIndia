-- Run once in the Supabase dashboard: SQL Editor -> New query -> paste -> Run.
--
-- Row-level security is enabled with no policies, so the public anon key can
-- read or write nothing. The app talks to these tables only from its server
-- with the service-role key stored in Streamlit secrets.

create table if not exists public.students (
    id          bigint generated always as identity primary key,
    owner_id    text not null,        -- sign-in provider's stable user id (the "sub" claim)
    owner_email text,
    name        text not null,
    target_role text,
    skills      text,
    created_at  timestamptz not null default now()
);
create index if not exists students_owner_id_idx on public.students (owner_id);

create table if not exists public.progress (
    student_id bigint not null references public.students (id) on delete cascade,
    skill      text not null,
    status     text not null,
    updated_at timestamptz not null default now(),
    primary key (student_id, skill)
);

create table if not exists public.feedback (
    id         bigint generated always as identity primary key,
    area       text,
    page       text,
    skill      text,
    details    text not null,
    expected   text,
    issue_url  text,
    user_email text,
    created_at timestamptz not null default now()
);

alter table public.students enable row level security;
alter table public.progress enable row level security;
alter table public.feedback enable row level security;
