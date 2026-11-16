from app.context.context_history import ContextHistory


print("Testing workflow context history...\n")


history = ContextHistory(max_history=5)


contexts = [
    "Development",
    "Browser / Research",
    "Media / Distraction",
    "Development"
]


for context in contexts:

    history.add_context(context)

    print(
        f"Added: {context}"
    )

    print(
        f"History: {history.get_history()}"
    )

    print()


print("Current context:")
print(history.get_current_context())

print("\nPrevious context:")
print(history.get_previous_context())