from typing import Dict, Type

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from scipy import stats

# Input schemas for validation


class PandasAnalysisInput(BaseModel):
    dataframe: pd.DataFrame = Field(..., description="DataFrame to analyze")
    operations: list = Field(
        default=['describe'], description="List of pandas operations to perform")


class NumpyAnalysisInput(BaseModel):
    data: list = Field(..., description="Numerical data to analyze")
    stats: list = Field(default=['mean', 'std'],
                        description="Statistics to calculate")


class VisualizationInput(BaseModel):
    data: pd.DataFrame = Field(..., description="Data to visualize")
    plot_type: str = Field(...,
                           description="Type of plot to generate (line|histogram|box)")


class StatisticalTestInput(BaseModel):
    data: list = Field(..., description="Numerical data for analysis")
    test_type: str = Field(
        ..., description="Statistical test to perform (ttest|mannwhitneyu|pearsonr)")


class PandasAnalysisTool(BaseTool):
    name: str = "Pandas Data Analysis"
    description: str = "Performs data manipulation and analysis using pandas. Useful for data cleaning, transformation, and basic statistical analysis."
    args_schema: Type[BaseModel] = PandasAnalysisInput

    def _run(self, dataframe: pd.DataFrame, operations: list) -> Dict:
        """Execute pandas operations with error handling and caching"""
        try:
            results = {}
            for op in operations:
                if hasattr(dataframe, op):
                    results[op] = getattr(dataframe, op)().to_dict()
                else:
                    raise ValueError(f"Invalid pandas operation: {op}")
            return results
        except Exception as e:
            return {"error": str(e)}


class NumpyAnalysisTool(BaseTool):
    name: str = "Numpy Numerical Analysis"
    description: str = "Performs numerical computations and statistical analysis using numpy. Ideal for array operations and mathematical transformations."
    args_schema: Type[BaseModel] = NumpyAnalysisInput

    def _run(self, data: list, stats: list) -> Dict:
        """Calculate numpy statistics with validation"""
        try:
            arr = np.array(data)
            results = {}
            for stat in stats:
                if hasattr(np, stat):
                    results[stat] = getattr(np, stat)(arr)
                else:
                    raise ValueError(f"Invalid numpy function: {stat}")
            return results
        except Exception as e:
            return {"error": str(e)}


class VisualizationTool(BaseTool):
    name: str = "Data Visualization"
    description: str = "Generates professional visualizations using matplotlib/seaborn. Creates line plots, histograms, and box plots."
    args_schema: Type[BaseModel] = VisualizationInput

    def _run(self, data: pd.DataFrame, plot_type: str) -> str:
        """Generate and save visualization with error handling"""
        try:
            filename = f"plot_{plot_type}_{pd.Timestamp.now().value}.png"
            plt.figure()

            if plot_type == 'line':
                sns.lineplot(data=data)
            elif plot_type == 'histogram':
                sns.histplot(data=data)
            elif plot_type == 'box':
                sns.boxplot(data=data)
            else:
                raise ValueError(f"Invalid plot type: {plot_type}")

            plt.savefig(filename)
            plt.close()
            return f"Visualization saved to {filename}"
        except Exception as e:
            return f"Visualization error: {str(e)}"


class StatisticalAnalysisTool(BaseTool):
    name: str = "Statistical Analysis"
    description: str = "Performs statistical tests using scipy. Supports t-tests, Mann-Whitney U, and Pearson correlation."
    args_schema: Type[BaseModel] = StatisticalTestInput

    def _run(self, data: list, test_type: str) -> Dict:
        """Execute statistical test with validation"""
        try:
            if test_type == 'ttest':
                result = stats.ttest_1samp(data, np.mean(data))
            elif test_type == 'mannwhitneyu':
                result = stats.mannwhitneyu(data, np.random.randn(len(data)))
            elif test_type == 'pearsonr':
                result = stats.pearsonr(data, np.arange(len(data)))
            else:
                raise ValueError(f"Unsupported test type: {test_type}")

            return {
                "test": test_type,
                "statistic": result.statistic,
                "pvalue": result.pvalue
            }
        except Exception as e:
            return {"error": str(e)}
