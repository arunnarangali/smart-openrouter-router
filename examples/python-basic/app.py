from smart_openrouter_router import SmartRouter


def main() -> None:
    with SmartRouter() as router:
        out = router.route_chat([
            {"role": "user", "content": "Give a short Python logging example."}
        ])
        print(out)


if __name__ == "__main__":
    main()
