# Asynchronous Crew Execution with `kickoff_for_each_async`

The `kickoff_for_each_async` method in `crew.py` allows for the concurrent execution of a crew's workflow for multiple sets of inputs. This is particularly useful when you need to process several independent scenarios in parallel, improving overall efficiency.

## How it Works

The method is defined as an asynchronous function:

```python
# filepath: /Users/mbp16/Desktop/CrewAI-fork/src/crewai/crew.py
# ...existing code...
    async def kickoff_for_each_async(self, inputs: List[Dict]) -> List[CrewOutput]:
        crew_copies = [self.copy() for _ in inputs]

        async def run_crew(crew, input_data):
            return await crew.kickoff_async(inputs=input_data)

        tasks = [
            asyncio.create_task(run_crew(crew_copies[i], inputs[i]))
            for i in range(len(inputs))
        ]

        results = await asyncio.gather(*tasks)

        total_usage_metrics = UsageMetrics()
        for crew in crew_copies:
            if crew.usage_metrics:
                total_usage_metrics.add_usage_metrics(crew.usage_metrics)

        self.usage_metrics = total_usage_metrics
        self._task_output_handler.reset()
        return results
# ...existing code...
```

Key steps in its operation:

1.  **Crew Duplication**: For each input dictionary in the `inputs` list, a deep copy of the original crew instance is created (`self.copy()`). This ensures that each concurrent execution runs in an isolated environment, preventing interference between them.
2.  **Asynchronous Task Creation**:
    *   An inner asynchronous function `run_crew` is defined. This function takes a crew copy and its corresponding input data, then calls `crew.kickoff_async(inputs=input_data)`. The `kickoff_async` method itself is designed to run a single crew execution asynchronously.
    *   For each `(crew_copy, input_data)` pair, `asyncio.create_task(run_crew(...))` is used. This schedules the `run_crew` coroutine to be run on the asyncio event loop as soon as possible. Each of these becomes an independent task that can run concurrently with others.
3.  **Concurrent Execution and Result Aggregation**:
    *   `results = await asyncio.gather(*tasks)` is the core of the concurrent execution. `asyncio.gather` takes a list of awaitables (in this case, the tasks created in the previous step) and runs them concurrently.
    *   It waits until all the tasks passed to it are complete.
    *   The `results` variable will then hold a list of the return values from each `run_crew` call (which are `CrewOutput` objects), in the same order as the original `inputs` list.
4.  **Metrics and Cleanup**:
    *   Usage metrics from all the crew copies are aggregated into `total_usage_metrics`.
    *   The main crew's `usage_metrics` are updated.
    *   The `_task_output_handler` is reset.
5.  **Return Value**: The method returns the `results` list, which is a `List[CrewOutput]`.

## How to Collect Results

To use `kickoff_for_each_async` and collect its results, you need to:

1.  **Call from an `async` function**: Since `kickoff_for_each_async` is an `async def` method, you must `await` it from within another asynchronous function.

    ```python
    import asyncio

    # Assuming 'my_crew' is an instance of your Crew class
    # and 'list_of_input_dictionaries' is a list of dictionaries,
    # where each dictionary represents a set of inputs for one crew run.

    async def run_multiple_crews_async():
        list_of_input_dictionaries = [
            {"topic": "AI in healthcare"},
            {"topic": "Renewable energy trends"},
            {"topic": "Future of remote work"}
        ]
        
        # Await the results from kickoff_for_each_async
        all_crew_outputs = await my_crew.kickoff_for_each_async(inputs=list_of_input_dictionaries)
        
        # Process the results
        for i, output in enumerate(all_crew_outputs):
            print(f"--- Output for Input Set {i+1} ---")
            print(f"Raw Output: {output.raw}")
            if output.pydantic:
                print(f"Pydantic Output: {output.pydantic}")
            # Access other parts of CrewOutput as needed (e.g., tasks_output, token_usage)
            print("\\n")

    # To run the async function:
    # asyncio.run(run_multiple_crews_async())
    ```

2.  **Iterate through the results**: The returned value is a list of `CrewOutput` objects. You can iterate through this list to access the outcome of each individual crew execution. Each `CrewOutput` object corresponds to one of the input dictionaries you provided, in the same order.

By using `kickoff_for_each_async`, you can significantly speed up processing when you have multiple independent tasks for your crew to perform, as they will be executed in parallel rather than sequentially.
